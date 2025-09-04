selector_to_html = {"a[href=\"#module-mcp.mixins.mcp_mixin\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mcp_mixin<a class=\"headerlink\" href=\"#module-mcp.mixins.mcp_mixin\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP mixin for adding Model Context Protocol capabilities to agents.</p><p>This module provides a mixin class that adds MCP functionality to any Haive agent.\nThe mixin handles server connections, tool discovery, resource access, and prompt\nmanagement with automatic error handling and graceful degradation.</p>", "a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#classes\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Classes<a class=\"headerlink\" href=\"#classes\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"../../../../configuration.html#haive.mcp.config.MCPConfig\"]": "<dt class=\"sig sig-object py\" id=\"haive.mcp.config.MCPConfig\">\n<em class=\"property\"><span class=\"k\"><span class=\"pre\">class</span></span><span class=\"w\"> </span></em><span class=\"sig-name descname\"><span class=\"pre\">MCPConfig</span></span><span class=\"sig-paren\">(</span><em class=\"sig-param\"><span class=\"o\"><span class=\"pre\">**</span></span><span class=\"n\"><span class=\"pre\">data</span></span><span class=\"p\"><span class=\"pre\">:</span></span><span class=\"w\"> </span><span class=\"n\"><a class=\"reference external\" href=\"https://docs.python.org/3/library/typing.html#typing.Any\" title=\"(in Python v3.13)\"><span class=\"pre\">Any</span></a></span></em><span class=\"sig-paren\">)</span> <span class=\"sig-return\"><span class=\"sig-return-icon\">\u2192</span> <span class=\"sig-return-typehint\"><a class=\"reference external\" href=\"https://docs.python.org/3/library/constants.html#None\" title=\"(in Python v3.13)\"><span class=\"pre\">None</span></a></span></span><a class=\"reference internal\" href=\"../../../../_modules/haive/mcp/config.html#MCPConfig\"><span class=\"viewcode-link\"><span class=\"pre\">[source]</span></span></a></dt><dd><p>Bases: <a class=\"reference external\" href=\"https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel\" title=\"(in Pydantic v0.0.0)\"><code class=\"xref py py-class docutils literal notranslate\"><span class=\"pre\">BaseModel</span></code></a></p><p>Complete MCP configuration for an agent.</p><p>This class provides the main configuration structure for MCP integration with Haive agents.\nIt controls server discovery, filtering, initialization, and runtime behavior.</p></dd>"}
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
