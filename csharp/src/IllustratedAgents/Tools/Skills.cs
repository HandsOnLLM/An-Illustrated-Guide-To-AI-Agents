namespace IllustratedAgents;

/// <summary>
/// A registry for tools and skills. A skill is a recipe in a folder with a SKILL.md file. The model
/// sees only its name and description (tier 1); calling it like a tool returns the full instructions
/// (tier 2) and the other files in the folder (tier 3). Chapter 5.
/// </summary>
public class Skills : NativeTools
{
    public Skills(IEnumerable<string>? requiresApproval = null, Func<string, bool>? approve = null)
        : base(requiresApproval, approve)
    {
    }

    /// <summary>Load the skill in <paramref name="skillDirectory"/> and register it as a tool with no parameters.</summary>
    public void AddSkill(string skillDirectory)
    {
        var directory = new DirectoryInfo(skillDirectory);
        var content = File.ReadAllText(Path.Combine(directory.FullName, "SKILL.md"));

        // TIER 2: instructions are everything after the frontmatter
        var parts = content.Split("---", 3);
        if (parts.Length < 3)
        {
            throw new FormatException($"{skillDirectory}/SKILL.md has no '---' frontmatter block.");
        }
        var frontmatter = ParseFrontmatter(parts[1]);
        var instructions = parts[2].Trim();

        // TIER 1: the catalog entry
        var name = frontmatter["name"];
        var description = "A skill. " + frontmatter["description"];

        // TIER 3: other files the agent can open
        var extraFiles = directory.GetFiles()
            .Select(file => file.Name)
            .Where(fileName => fileName != "SKILL.md")
            .Order()
            .ToList();

        // When activated, return the instructions plus the folder context
        Func<string> skill = () => $"""
            {instructions}

            Skill folder: {directory.FullName}

            Available files: [{string.Join(", ", extraFiles)}]
            """;
        AddTool(name, skill, description);
    }

    public override string Prompt
    {
        get
        {
            return """
                You have specialized skills available.
                To activate a skill, call it with an empty argument object.
                Skills return instructions; they do not process the task directly.
                """;
        }
    }

    /// <summary>Reads simple <c>key: value</c> lines, which is all SKILL.md frontmatter needs here.</summary>
    public static Dictionary<string, string> ParseFrontmatter(string text)
    {
        var result = new Dictionary<string, string>();
        foreach (var line in text.Split('\n'))
        {
            var colon = line.IndexOf(':');
            if (colon > 0)
            {
                result[line[..colon].Trim()] = line[(colon + 1)..].Trim();
            }
        }
        return result;
    }
}
