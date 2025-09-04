selector_to_html = {"a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#module-mcp.cli.mcp_manager\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mcp_manager<a class=\"headerlink\" href=\"#module-mcp.cli.mcp_manager\" title=\"Link to this heading\">\u00b6</a></h1><p>Comprehensive MCP Server Manager.</p><p>This script provides a complete management interface for MCP servers including:\n- Discovery from multiple sources\n- Installation using various methods\n- Configuration management\n- Health monitoring\n- Updates and maintenance</p>", "a[href=\"#classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Classes<a class=\"headerlink\" href=\"#classes\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#functions\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Functions<a class=\"headerlink\" href=\"#functions\" title=\"Link to this heading\">\u00b6</a></h2>"}
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
