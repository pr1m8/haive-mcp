selector_to_html = {"a[href=\"#module-summary\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Module Summary<a class=\"headerlink\" href=\"#module-summary\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#module-mcp.agents\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">agents<a class=\"headerlink\" href=\"#module-mcp.agents\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"intelligent_mcp_agent/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">intelligent_mcp_agent<a class=\"headerlink\" href=\"#module-mcp.agents.intelligent_mcp_agent\" title=\"Link to this heading\">\u00b6</a></h1><p>Intelligent MCP Agent for dynamic server discovery and management.</p><p>This module provides an advanced agent that can dynamically discover, recommend,\ninstall, and manage MCP servers based on user needs. It includes HITL (Human-In-The-Loop)\napproval workflows and intelligent capability matching.</p>", "a[href=\"mcp_agent/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">mcp_agent<a class=\"headerlink\" href=\"#module-mcp.agents.mcp_agent\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP Agent - Phase 4 Integration.</p><p>This agent demonstrates the complete MCP integration workflow:\n1. Uses MCPManager to install and connect to MCP servers\n2. Dynamically discovers and registers MCP tools\n3. Integrates with Haive SimpleAgent for LLM-powered reasoning\n4. Provides seamless tool execution through MCP protocol</p>", "a[href=\"basic_mcp_agent/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">basic_mcp_agent<a class=\"headerlink\" href=\"#module-mcp.agents.basic_mcp_agent\" title=\"Link to this heading\">\u00b6</a></h1><p>Basic MCP-enabled agent implementation that demonstrates integration with haive-agents.</p><p>This module provides a ready-to-use agent class that combines SimpleAgent capabilities\nwith MCP (Model Context Protocol) support. The BasicMCPAgent class offers seamless\nintegration with MCP servers, automatic tool discovery, and convenient factory methods.</p>", "a[href=\"transferable_mcp_agent/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">transferable_mcp_agent<a class=\"headerlink\" href=\"#module-mcp.agents.transferable_mcp_agent\" title=\"Link to this heading\">\u00b6</a></h1><p>Transferable MCP agent implementation with resource/prompt/tool sharing capabilities.</p><p>This module provides an advanced MCP agent that supports sharing and transferring\ncapabilities between agent instances. It enables collaborative workflows where multiple\nagents can share MCP clients, tools, resources, and prompts for efficient distributed\nprocessing.</p>", "a[href=\"documentation_agent/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">documentation_agent<a class=\"headerlink\" href=\"#module-mcp.agents.documentation_agent\" title=\"Link to this heading\">\u00b6</a></h1><p>MCP Documentation Agent for processing and setting up MCP servers.</p><p>This module provides a specialized agent that combines document processing\ncapabilities with MCP knowledge to help users understand, configure, and\nimplement MCP servers. It processes documentation from various sources and\ngenerates actionable setup instructions.</p>"}
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
