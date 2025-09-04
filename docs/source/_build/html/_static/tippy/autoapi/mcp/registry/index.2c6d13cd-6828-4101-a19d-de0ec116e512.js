selector_to_html = {"a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#key-features\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Key Features<a class=\"headerlink\" href=\"#key-features\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#registry-operations\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Registry Operations<a class=\"headerlink\" href=\"#registry-operations\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"../../../api/generated/haive.mcp.downloader.html#module-haive.mcp.downloader\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">haive.mcp.downloader<a class=\"headerlink\" href=\"#module-haive.mcp.downloader\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"#module-mcp.registry\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">registry<a class=\"headerlink\" href=\"#module-mcp.registry\" title=\"Link to this heading\">\u00b6</a></h1><p>Registry Management for MCP Servers.</p><p>This module provides comprehensive tools for managing the MCP server registry,\nsupporting the transition from Git-based to NPM package-based server distribution.</p>", "a[href=\"#classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Classes<a class=\"headerlink\" href=\"#classes\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#available-classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Available Classes<a class=\"headerlink\" href=\"#available-classes\" title=\"Link to this heading\">\u00b6</a></h2><h3>Server Management<a class=\"headerlink\" href=\"#server-management\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"server_converter/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">server_converter<a class=\"headerlink\" href=\"#module-mcp.registry.server_converter\" title=\"Link to this heading\">\u00b6</a></h1><p>Server Registry Converter for Phase 3+.</p><p>This module converts GitHub-based server entries from the 1900+ server database\ninto npm package format for the MCP Manager registry.</p>", "a[href=\"#server-management\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Server Management<a class=\"headerlink\" href=\"#server-management\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#usage-example\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Usage Example<a class=\"headerlink\" href=\"#usage-example\" title=\"Link to this heading\">\u00b6</a></h2>"}
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
