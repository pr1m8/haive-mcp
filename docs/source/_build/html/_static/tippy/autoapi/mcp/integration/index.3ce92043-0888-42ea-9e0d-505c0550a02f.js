selector_to_html = {"a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"integrated_mcp_system/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">integrated_mcp_system<a class=\"headerlink\" href=\"#module-mcp.integration.integrated_mcp_system\" title=\"Link to this heading\">\u00b6</a></h1><p>Integrated MCP Discovery &amp; Management System.</p><p>A complete end-to-end solution that combines:\n1. MCP server discovery with enhanced RAG search\n2. One-click installation from discovery results\n3. FastMCP server management (like Claude\u2019s \u2018claude mcp add\u2019)\n4. Live server monitoring and access</p>", "a[href=\"aug_llm_mcp_extension/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">aug_llm_mcp_extension<a class=\"headerlink\" href=\"#module-mcp.integration.aug_llm_mcp_extension\" title=\"Link to this heading\">\u00b6</a></h1><p>Extension module to add MCP support to AugLLMConfig.</p><p>This module provides utilities and mixins to enhance AugLLMConfig with MCP\nintegration capabilities, allowing seamless use of MCP tools, resources, and\nprompts within the Haive agent framework.</p>", "a[href=\"fastapi_mcp_server/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">fastapi_mcp_server<a class=\"headerlink\" href=\"#module-mcp.integration.fastapi_mcp_server\" title=\"Link to this heading\">\u00b6</a></h1><p>FastAPI MCP Discovery and Installation Server.</p><p>This server provides:\n1. Web interface for discovering MCP servers\n2. HITL approval via web UI\n3. Server installation and testing\n4. Real-time status updates via WebSocket</p>", "a[href=\"#module-mcp.integration\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">integration<a class=\"headerlink\" href=\"#module-mcp.integration\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP integration module.</p>", "a[href=\"haive_agent_mcp_integration/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">haive_agent_mcp_integration<a class=\"headerlink\" href=\"#module-mcp.integration.haive_agent_mcp_integration\" title=\"Link to this heading\">\u00b6</a></h1><p>Haive Agent + MCP Tool Integration.</p><p>Demonstrates the complete workflow:\n1. Discover an MCP server/tool\n2. Install and configure it\n3. Create a haive agent that uses the MCP tool\n4. Show the agent executing with the discovered tool</p>", "a[href=\"integrated_launcher/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">integrated_launcher<a class=\"headerlink\" href=\"#module-mcp.integration.integrated_launcher\" title=\"Link to this heading\">\u00b6</a></h1><p>Integrated MCP System Launcher.</p><p>Provides easy access to all components of the integrated MCP discovery and management system.</p>"}
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
