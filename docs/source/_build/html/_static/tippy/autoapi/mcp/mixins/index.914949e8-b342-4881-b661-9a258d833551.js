selector_to_html = {"a[href=\"#module-mcp.mixins\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mixins<a class=\"headerlink\" href=\"#module-mcp.mixins\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"mcp_mixin/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mcp_mixin<a class=\"headerlink\" href=\"#module-mcp.mixins.mcp_mixin\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP mixin for adding Model Context Protocol capabilities to agents.</p><p>This module provides a mixin class that adds MCP functionality to any Haive agent.\nThe mixin handles server connections, tool discovery, resource access, and prompt\nmanagement with automatic error handling and graceful degradation.</p>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>"}
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
