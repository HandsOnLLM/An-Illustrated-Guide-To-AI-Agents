using System.ComponentModel;
using System.Globalization;

namespace IllustratedAgents;

/// <summary>
/// Every simple tool from the book, in one place so any chapter can register them. Provided for you,
/// like the Python <c>toolbox.py</c>.
/// </summary>
/// <remarks>
/// Numbers come in as strings on purpose, as in the book: small models are more reliable at copying text
/// than at producing well-typed JSON numbers.
/// </remarks>
public static class Toolbox
{
    [Description("Get the current weather for a location.")]
    public static string GetWeather(string location)
    {
        var temperature = Random.Shared.Next(10, 31);
        string[] statuses = ["Sunny", "Cloudy", "Rainy"];
        var status = statuses[Random.Shared.Next(statuses.Length)];
        return $"Weather in {location}: {status}, {temperature}℃";
    }

    [Description("Add two numbers.")]
    public static double Add(string a, string b) => Parse(a) + Parse(b);

    [Description("Subtract two numbers.")]
    public static double Subtract(string a, string b) => Parse(a) - Parse(b);

    [Description("Multiply two numbers.")]
    public static double Multiply(string a, string b) => Parse(a) * Parse(b);

    [Description("Return today's date (YYYY-MM-DD).")]
    public static string Today() => DateOnly.FromDateTime(DateTime.Today).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    [Description("Days between two ISO dates.")]
    public static int DaysBetween(string a, string b) =>
        DateOnly.ParseExact(b, "yyyy-MM-dd", CultureInfo.InvariantCulture).DayNumber
        - DateOnly.ParseExact(a, "yyyy-MM-dd", CultureInfo.InvariantCulture).DayNumber;

    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(30) };

    [Description("Read the content of a markdown file from a web address or a local path.")]
    public static async Task<string> ReadMarkdown([Description("The path or URL of the markdown file.")] string path)
    {
        if (path.StartsWith("http://") || path.StartsWith("https://"))
        {
            return await Http.GetStringAsync(path);
        }
        return await File.ReadAllTextAsync(path);
    }

    private static double Parse(string number) =>
        double.Parse(number.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture);
}
