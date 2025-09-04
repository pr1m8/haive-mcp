selector_to_html = {"a[href=\"#module-mcp.cli\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">cli<a class=\"headerlink\" href=\"#module-mcp.cli\" title=\"Link to this heading\">\u00b6</a></h1><p>CLI utilities for haive-mcp.</p>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"server_manager/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">server_manager<a class=\"headerlink\" href=\"#module-mcp.cli.server_manager\" title=\"Link to this heading\">\u00b6</a></h1><p>CLI for MCP Server Manager.</p><p>This provides a command-line interface to manage MCP servers.</p>", "a[href=\"mcp_manager/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mcp_manager<a class=\"headerlink\" href=\"#module-mcp.cli.mcp_manager\" title=\"Link to this heading\">\u00b6</a></h1><p>Comprehensive MCP Server Manager.</p><p>This script provides a complete management interface for MCP servers including:\n- Discovery from multiple sources\n- Installation using various methods\n- Configuration management\n- Health monitoring\n- Updates and maintenance</p>"}
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
