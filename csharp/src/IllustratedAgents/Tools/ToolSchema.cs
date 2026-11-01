using System.ComponentModel;
using System.Reflection;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Builds an OpenAI-style function definition from a C# delegate: the C# version of Python's
/// <c>tool_to_schema</c>. Chapter 5, native tool calling.
/// </summary>
public static class ToolSchema
{
    /// <summary>
    /// The schema for one tool. The name is the name you registered (C# method names are PascalCase,
    /// and lambdas have compiler-generated names). The description comes from a
    /// <see cref="DescriptionAttribute"/> on the method, or falls back to <paramref name="fallbackDescription"/>.
    /// </summary>
    public static JsonObject FromDelegate(string name, Delegate function, string fallbackDescription = "")
    {
        var properties = new JsonObject();
        var required = new JsonArray();

        // Extract metadata from each parameter
        foreach (var parameter in function.Method.GetParameters())
        {
            if (parameter.ParameterType == typeof(CancellationToken))
            {
                continue; // supplied by the agent, never by the model
            }

            var property = new JsonObject { ["type"] = JsonTypeOf(parameter.ParameterType) };
            if (parameter.GetCustomAttribute<DescriptionAttribute>()?.Description is { } parameterDescription)
            {
                property["description"] = parameterDescription;
            }
            properties[parameter.Name!] = property;

            if (!parameter.HasDefaultValue)
            {
                required.Add(parameter.Name!);
            }
        }

        // Fill the schema
        var description = function.Method.GetCustomAttribute<DescriptionAttribute>()?.Description ?? fallbackDescription;
        return new JsonObject
        {
            ["type"] = "function",
            ["function"] = new JsonObject
            {
                ["name"] = name,
                ["description"] = description,
                ["parameters"] = new JsonObject
                {
                    ["type"] = "object",
                    ["properties"] = properties,
                    ["required"] = required,
                },
            },
        };
    }

    /// <summary>Maps a C# type to a JSON Schema type name, the way Python's <c>TYPE_MAP</c> does.</summary>
    public static string JsonTypeOf(Type type)
    {
        type = Nullable.GetUnderlyingType(type) ?? type;

        if (type == typeof(string)) return "string";
        if (type == typeof(bool)) return "boolean";
        if (type == typeof(int) || type == typeof(long) || type == typeof(short)) return "integer";
        if (type == typeof(double) || type == typeof(float) || type == typeof(decimal)) return "number";
        if (type.IsArray || (type != typeof(string) && typeof(System.Collections.IEnumerable).IsAssignableFrom(type))) return "array";
        return "object";
    }
}
