selector_to_html = {"a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#module-mcp.installers\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">installers<a class=\"headerlink\" href=\"#module-mcp.installers\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"safe_pattern_installer/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">safe_pattern_installer<a class=\"headerlink\" href=\"#module-mcp.installers.safe_pattern_installer\" title=\"Link to this heading\">\u00b6</a></h1><p>Safe Pattern-Based MCP Server Installer.</p><p>Version 1: Uses predefined patterns for safe, predictable installations.\nNo code generation - only trusted, tested patterns.</p>", "a[href=\"advanced_code_installer/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">advanced_code_installer<a class=\"headerlink\" href=\"#module-mcp.installers.advanced_code_installer\" title=\"Link to this heading\">\u00b6</a></h1><p>Advanced Code-Generating MCP Server Installer.</p><p>Version 2: Uses Aug_LLM agents to generate custom installation code.\nMore flexible but requires human oversight for safety.</p>", "a[href=\"config_manager/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">config_manager<a class=\"headerlink\" href=\"#module-mcp.installers.config_manager\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP Configuration and Environment Management.</p><p>Handles .env files, configuration templates, and secure credential storage.</p>"}
skip_classes = ["headerlink", "sd-stretched-link", "reference-external"]

window.onload = function () {
    for (const [select, tip_html] of Object.entries(selector_to_html)) {
        const links = document.querySelectorAll(`div.content ${select}`);
        for (const link of links) {
            if (skip_classes.some(c => link.classList.contains(c))) {
                continue;
            }
            link.classList.add('has-tooltip');
            tippy(link, {
                content: tip_html,
                allowHTML: true,
                arrow: true,
                placement: 'auto-start', maxWidth: 600, interactive: true, theme: 'light-border', delay: [200, 100], duration: [200, 100],
                onShow(instance) {MathJax.typesetPromise([instance.popper]).then(() => {});},
            });
        };
    };
    console.log("tippy tips loaded!");
};
