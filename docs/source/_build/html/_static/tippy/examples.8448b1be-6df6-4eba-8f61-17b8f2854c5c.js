selector_to_html = {"a[href=\"#automation-discovery\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Automation &amp; Discovery<a class=\"headerlink\" href=\"#automation-discovery\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#example-scripts\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Example Scripts<a class=\"headerlink\" href=\"#example-scripts\" title=\"Link to this heading\">\u00b6</a></h2><p>Our examples directory contains working scripts that demonstrate various MCP integration patterns:</p>", "a[href=\"#next-steps\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Next Steps<a class=\"headerlink\" href=\"#next-steps\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#running-examples\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Running Examples<a class=\"headerlink\" href=\"#running-examples\" title=\"Link to this heading\">\u00b6</a></h2><p>To run any example:</p>", "a[href=\"#advanced-integration\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Advanced Integration<a class=\"headerlink\" href=\"#advanced-integration\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#configuration\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Configuration<a class=\"headerlink\" href=\"#configuration\" title=\"Link to this heading\">\u00b6</a></h2><p>Some examples use the <code class=\"docutils literal notranslate\"><span class=\"pre\">mcp_servers_config.json</span></code> file for configuration. This file defines server categories and installation preferences.</p>", "a[href=\"tutorials.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Tutorials<a class=\"headerlink\" href=\"#tutorials\" title=\"Link to this heading\">\u00b6</a></h1><p>Welcome to the haive-mcp tutorials! These hands-on guides will walk you through using the Model Context Protocol (MCP) with Haive\u2019s 1900+ available servers.</p>", "a[href=\"#examples\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Examples<a class=\"headerlink\" href=\"#examples\" title=\"Link to this heading\">\u00b6</a></h1><p>Comprehensive examples demonstrating haive-mcp capabilities with 1900+ MCP servers.</p>", "a[href=\"#basic-examples\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Basic Examples<a class=\"headerlink\" href=\"#basic-examples\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#production-examples\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Production Examples<a class=\"headerlink\" href=\"#production-examples\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#quick-example\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Quick Example<a class=\"headerlink\" href=\"#quick-example\" title=\"Link to this heading\">\u00b6</a></h2><p>Here\u2019s a simple example to get started:</p>", "a[href=\"#specialized-use-cases\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Specialized Use Cases<a class=\"headerlink\" href=\"#specialized-use-cases\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"guides.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Guides<a class=\"headerlink\" href=\"#guides\" title=\"Link to this heading\">\u00b6</a></h1><p>In-depth guides for working with haive-mcp and its 1900+ available MCP servers.</p>"}
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
