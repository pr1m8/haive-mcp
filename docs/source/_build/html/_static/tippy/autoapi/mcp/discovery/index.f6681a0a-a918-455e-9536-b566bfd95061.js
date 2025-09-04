selector_to_html = {"a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"installed_servers/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">installed_servers<a class=\"headerlink\" href=\"#module-mcp.discovery.installed_servers\" title=\"Link to this heading\">\u00b6</a></h1><p>Discover and manage installed MCP servers.</p><p>This module provides utilities to find, check, and manage MCP servers\nthat are already installed on the system.</p>", "a[href=\"#classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Classes<a class=\"headerlink\" href=\"#classes\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"server_discovery/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">server_discovery<a class=\"headerlink\" href=\"#module-mcp.discovery.server_discovery\" title=\"Link to this heading\">\u00b6</a></h1><p>Simple MCP server discovery placeholder.</p><p>This module provides a placeholder implementation for MCP server discovery\nfunctionality. In a full implementation, this would handle automatic discovery\nof available MCP servers from various sources like registries, local installations,\nand configured directories.</p>", "a[href=\"#functions\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Functions<a class=\"headerlink\" href=\"#functions\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#module-mcp.discovery\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">discovery<a class=\"headerlink\" href=\"#module-mcp.discovery\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"analyzer/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">analyzer<a class=\"headerlink\" href=\"#module-mcp.discovery.analyzer\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP server analyzer for component discovery integration.</p><p>This module provides analysis capabilities for discovering and configuring MCP\nservers from various sources. It can analyze dictionaries, objects, and files\nto extract valid MCP server configurations.</p>"}
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
