selector_to_html = {"a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#key-features\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Key Features<a class=\"headerlink\" href=\"#key-features\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#available-plugins\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Available Plugins<a class=\"headerlink\" href=\"#available-plugins\" title=\"Link to this heading\">\u00b6</a></h2><h3>Browser Plugin<a class=\"headerlink\" href=\"#browser-plugin\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#plugin-registry\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Plugin Registry<a class=\"headerlink\" href=\"#plugin-registry\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"browser_plugin/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">browser_plugin<a class=\"headerlink\" href=\"#module-mcp.plugins.browser_plugin\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP Browser Plugin - Manage Our 63 Downloaded MCP Servers</p><p>This plugin inherits from PluginPlatform and specializes in managing the 63 MCP servers\nwe successfully downloaded using our bulk installer. It implements the intelligent\ninheritance pattern from our architecture plan.</p>", "a[href=\"#classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Classes<a class=\"headerlink\" href=\"#classes\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#browser-plugin\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Browser Plugin<a class=\"headerlink\" href=\"#browser-plugin\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#base-inheritance-chain\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Base Inheritance Chain<a class=\"headerlink\" href=\"#base-inheritance-chain\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#plugin-architecture\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Plugin Architecture<a class=\"headerlink\" href=\"#plugin-architecture\" title=\"Link to this heading\">\u00b6</a></h2><h3>Base Inheritance Chain<a class=\"headerlink\" href=\"#base-inheritance-chain\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#module-mcp.plugins\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">plugins<a class=\"headerlink\" href=\"#module-mcp.plugins\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP Plugins Module.</p><p>This module provides plugin implementations for the unified MCP platform architecture.\nAll plugins inherit from PluginPlatform and implement the Pydantic-first design pattern\nwith intelligent inheritance from our Phase 1 base platform models.</p>"}
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
