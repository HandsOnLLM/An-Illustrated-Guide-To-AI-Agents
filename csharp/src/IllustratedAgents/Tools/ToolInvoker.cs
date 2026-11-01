using System.Globalization;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Calls a C# delegate with the JSON arguments a model produced: C#'s answer to Python's
/// <c>tool_func(**kwargs)</c>. Provided for you: it's reflection plumbing, not an agent concept.
/// </summary>
/// <remarks>
/// Arguments are matched to parameters by name. A tool whose only parameter is a <see cref="JsonObject"/>
/// receives all of its arguments as one object (MCP tools use this). Async tools are awaited.
/// </remarks>
public static class ToolInvoker
{
    private static readonly JsonSerializerOptions Lenient = new()
    {
        PropertyNameCaseInsensitive = true,
        NumberHandling = System.Text.Json.Serialization.JsonNumberHandling.AllowReadingFromString,
    };

    public static async Task<object?> InvokeAsync(Delegate function, JsonNode? kwargs, CancellationToken cancellationToken = default)
    {
        var parameters = function.Method.GetParameters();
        var arguments = BindArguments(parameters, kwargs, cancellationToken);

        object? result;
        try
        {
            result = function.DynamicInvoke(arguments);
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            // Surface the tool's own exception, not the reflection wrapper around it.
            System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }

        return await UnwrapAsync(result);
    }

    /// <summary>Formats a tool result the way the model will read it.</summary>
    public static string Format(object? result) => result switch
    {
        null => "None",
        string text => text,
        bool flag => flag ? "True" : "False",
        IFormattable formattable => formattable.ToString(null, CultureInfo.InvariantCulture),
        JsonNode node => node.ToJsonString(TrajectoryView.Readable),
        _ => result.ToString() ?? "",
    };

    private static object?[] BindArguments(ParameterInfo[] parameters, JsonNode? kwargs, CancellationToken cancellationToken)
    {
        // A tool whose only real parameter is a JsonObject takes every argument at once.
        var takesRawArguments = parameters.Count(p => p.ParameterType != typeof(CancellationToken)) == 1
            && parameters.Any(p => p.ParameterType == typeof(JsonObject));

        var byName = kwargs as JsonObject;
        var values = new object?[parameters.Length];
        for (var i = 0; i < parameters.Length; i++)
        {
            var parameter = parameters[i];

            if (parameter.ParameterType == typeof(CancellationToken))
            {
                values[i] = cancellationToken;
            }
            else if (takesRawArguments)
            {
                values[i] = byName?.DeepClone().AsObject() ?? new JsonObject();
            }
            else if (byName is not null && TryGet(byName, parameter.Name!, out var node))
            {
                values[i] = Convert(node, parameter.ParameterType);
            }
            else if (byName is null && kwargs is JsonValue single && parameters.Length == 1)
            {
                // Some models send a bare value for a one-argument tool.
                values[i] = Convert(single, parameter.ParameterType);
            }
            else if (parameter.HasDefaultValue)
            {
                values[i] = parameter.DefaultValue;
            }
            else
            {
                throw new ArgumentException($"Missing argument '{parameter.Name}'.");
            }
        }
        return values;
    }

    private static bool TryGet(JsonObject json, string name, out JsonNode? node)
    {
        foreach (var (key, value) in json)
        {
            if (string.Equals(key, name, StringComparison.OrdinalIgnoreCase))
            {
                node = value;
                return true;
            }
        }
        node = null;
        return false;
    }

    private static object? Convert(JsonNode? node, Type type)
    {
        if (node is null)
        {
            return null;
        }

        // Models often send numbers for string parameters and strings for number parameters.
        if (type == typeof(string))
        {
            return node is JsonValue value && value.TryGetValue<string>(out var text) ? text : node.ToJsonString();
        }

        return node.Deserialize(type, Lenient);
    }

    private static async Task<object?> UnwrapAsync(object? result)
    {
        if (result is not Task task)
        {
            return result;
        }

        await task;
        var resultProperty = task.GetType().GetProperty("Result");
        var value = resultProperty?.GetValue(task);

        // A plain Task has a hidden "VoidTaskResult" result; treat it as no result.
        return value?.GetType().Name == "VoidTaskResult" ? null : value;
    }
}
