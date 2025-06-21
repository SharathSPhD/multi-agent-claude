"""
Command line interface for the multi-agent system.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .config import SystemConfig, AgentConfig, create_default_config
from .core import Orchestrator, MCPAgent
from .memory import SystemMemory
from .a2a import A2AServer

console = Console()
logger = structlog.get_logger(__name__)

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Multi-Agent System with mcp-agent, A2A protocol, and MCP integration."""
    
    # Set up logging
    level = "DEBUG" if verbose else "INFO"
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level)
    )
    
    # Load configuration
    if config:
        config_path = Path(config)
        system_config = SystemConfig.load_from_file(config_path)
    else:
        # Use default configuration
        system_config = create_default_config()
    
    ctx.ensure_object(dict)
    ctx.obj['config'] = system_config


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the multi-agent system with default configuration."""
    config: SystemConfig = ctx.obj['config']
    
    config_path = config.base_path / "config.yaml"
    
    try:
        # Create base directory
        config.base_path.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config.save_to_file(config_path)
        
        rprint(Panel.fit(
            f"✅ Multi-agent system initialized!\n\n"
            f"📁 Base path: {config.base_path}\n"
            f"⚙️  Config file: {config_path}\n"
            f"🤖 Agents configured: {len(config.agents)}\n"
            f"🔧 MCP servers: {len(config.mcp_servers)}",
            title="Initialization Complete"
        ))
        
        # Show agent summary
        table = Table(title="Configured Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Capabilities", style="yellow")
        
        for agent_name, agent_config in config.agents.items():
            capabilities = ", ".join(agent_config.capabilities[:3])
            if len(agent_config.capabilities) > 3:
                capabilities += f" (+{len(agent_config.capabilities) - 3} more)"
            
            table.add_row(
                agent_name,
                agent_config.type,
                agent_config.description[:50] + "..." if len(agent_config.description) > 50 else agent_config.description,
                capabilities
            )
        
        console.print(table)
        
    except Exception as e:
        rprint(f"❌ [red]Error initializing system: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def start(ctx):
    """Start the multi-agent system orchestrator."""
    config: SystemConfig = ctx.obj['config']
    
    async def run_orchestrator():
        try:
            rprint("🚀 [green]Starting multi-agent system...[/green]")
            
            # Initialize system memory
            system_memory = SystemMemory(config.memory_path)
            await system_memory.initialize()
            
            # Initialize orchestrator
            orchestrator = Orchestrator(config)
            await orchestrator.initialize()
            
            rprint(f"✅ [green]System started with {len(orchestrator.agents)} agents[/green]")
            
            # Start A2A server if configured
            if config.a2a_port:
                a2a_server = A2AServer(config.a2a_host, config.a2a_port)
                
                # Register handlers for each agent
                for agent_name, agent in orchestrator.agents.items():
                    a2a_server.register_message_handler(agent_name, agent.communicate_with_agent)
                    a2a_server.register_task_handler(agent_name, agent.execute_task)
                
                rprint(f"🌐 [blue]A2A server starting on {config.a2a_host}:{config.a2a_port}[/blue]")
                await a2a_server.start()
            else:
                # Keep running for manual task submission
                rprint("💤 [yellow]Orchestrator running. Press Ctrl+C to stop.[/yellow]")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
            
        except Exception as e:
            rprint(f"❌ [red]Error starting system: {e}[/red]")
        finally:
            if 'orchestrator' in locals():
                await orchestrator.shutdown()
            rprint("🛑 [yellow]System stopped[/yellow]")
    
    asyncio.run(run_orchestrator())


@cli.command()
@click.option('--task-file', '-f', type=click.Path(exists=True), help='Task file (JSON/YAML)')
@click.option('--description', '-d', help='Task description')
@click.option('--agent', '-a', help='Target agent name')
@click.option('--type', '-t', default='general', help='Task type')
@click.pass_context
def submit(ctx, task_file, description, agent, type):
    """Submit a task to the multi-agent system."""
    config: SystemConfig = ctx.obj['config']
    
    if task_file:
        # Load task from file
        task_path = Path(task_file)
        with open(task_path, 'r') as f:
            if task_path.suffix.lower() in ['.yaml', '.yml']:
                task_data = yaml.safe_load(f)
            else:
                task_data = json.load(f)
    else:
        # Create task from CLI arguments
        if not description:
            rprint("❌ [red]Either --task-file or --description is required[/red]")
            sys.exit(1)
        
        task_data = {
            "description": description,
            "type": type,
            "agent": agent or "orchestrator"
        }
    
    async def submit_task():
        try:
            # Initialize orchestrator
            orchestrator = Orchestrator(config)
            await orchestrator.initialize()
            
            # Submit task
            task_id = await orchestrator.submit_task(task_data)
            
            rprint(f"✅ [green]Task submitted successfully![/green]")
            rprint(f"📋 Task ID: {task_id}")
            
            # Wait for result (with timeout)
            timeout = 60  # seconds
            for i in range(timeout):
                result = await orchestrator.get_task_result(task_id)
                if result:
                    if result.success:
                        rprint(f"✅ [green]Task completed successfully![/green]")
                        rprint(f"📋 Result: {result.result}")
                    else:
                        rprint(f"❌ [red]Task failed: {result.error}[/red]")
                    break
                
                await asyncio.sleep(1)
                if i % 10 == 0:
                    rprint(f"⏳ [yellow]Waiting for task completion... ({i}s)[/yellow]")
            else:
                rprint(f"⏰ [yellow]Task is still running after {timeout}s[/yellow]")
            
        except Exception as e:
            rprint(f"❌ [red]Error submitting task: {e}[/red]")
        finally:
            await orchestrator.shutdown()
    
    asyncio.run(submit_task())


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and agent information."""
    config: SystemConfig = ctx.obj['config']
    
    # System configuration summary
    rprint(Panel.fit(
        f"🏠 Base Path: {config.base_path}\n"
        f"🧠 Memory Path: {config.memory_path}\n"
        f"🌐 A2A Server: {config.a2a_host}:{config.a2a_port}\n"
        f"🎯 Orchestrator: {config.orchestrator_agent}\n"
        f"⚡ Max Concurrent Tasks: {config.max_concurrent_tasks}",
        title="System Configuration"
    ))
    
    # Agent status table
    table = Table(title="Agent Status")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Memory Store", style="yellow")
    table.add_column("MCP Servers", style="blue")
    
    for agent_name, agent_config in config.agents.items():
        status_emoji = "✅" if agent_config.enabled else "❌"
        status_text = "Enabled" if agent_config.enabled else "Disabled"
        
        table.add_row(
            agent_name,
            agent_config.type,
            f"{status_emoji} {status_text}",
            agent_config.memory_store,
            ", ".join(agent_config.mcp_servers)
        )
    
    console.print(table)
    
    # MCP servers table
    mcp_table = Table(title="MCP Servers")
    mcp_table.add_column("Name", style="cyan")
    mcp_table.add_column("Command", style="green")
    mcp_table.add_column("Args", style="yellow")
    
    for server_name, server_config in config.mcp_servers.items():
        mcp_table.add_row(
            server_name,
            server_config.command,
            " ".join(server_config.args)
        )
    
    console.print(mcp_table)


@cli.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--type', required=True, help='Agent type')
@click.option('--description', required=True, help='Agent description')
@click.option('--capabilities', help='Comma-separated capabilities')
@click.option('--mcp-servers', help='Comma-separated MCP server names')
@click.pass_context
def add_agent(ctx, name, type, description, capabilities, mcp_servers):
    """Add a new agent to the configuration."""
    config: SystemConfig = ctx.obj['config']
    
    if name in config.agents:
        rprint(f"❌ [red]Agent {name} already exists[/red]")
        sys.exit(1)
    
    # Create agent configuration
    agent_config = AgentConfig(
        name=name,
        type=type,
        description=description,
        capabilities=capabilities.split(',') if capabilities else [],
        mcp_servers=mcp_servers.split(',') if mcp_servers else [],
        memory_store=f"{name}_memory"
    )
    
    # Add to system config
    config.add_agent(agent_config)
    
    # Save configuration
    config_path = config.base_path / "config.yaml"
    config.save_to_file(config_path)
    
    rprint(f"✅ [green]Agent {name} added successfully![/green]")


@cli.command()
@click.option('--agent', help='Specific agent name')
@click.pass_context
def memory(ctx, agent):
    """Show memory statistics for agents."""
    config: SystemConfig = ctx.obj['config']
    
    async def show_memory():
        try:
            system_memory = SystemMemory(config.memory_path)
            await system_memory.initialize()
            
            if agent:
                # Show specific agent memory
                agent_memory = await system_memory.get_agent_memory(agent)
                stats = await agent_memory.get_task_statistics()
                
                rprint(Panel.fit(
                    f"📊 Total Tasks: {stats['total_tasks']}\n"
                    f"✅ Completed: {stats['completed_tasks']}\n"
                    f"⏳ Pending: {stats['pending_tasks']}\n"
                    f"📈 Completion Rate: {stats['completion_rate']:.1%}",
                    title=f"Memory Statistics - {agent}"
                ))
            else:
                # Show system-wide memory
                stats = await system_memory.get_system_statistics()
                
                rprint(Panel.fit(
                    f"🤖 Active Agents: {stats['agent_count']}\n"
                    f"📋 System Events: {stats['total_events']}",
                    title="System Memory Statistics"
                ))
                
                # Agent memory table
                table = Table(title="Agent Memory Statistics")
                table.add_column("Agent", style="cyan")
                table.add_column("Total Tasks", style="green")
                table.add_column("Completed", style="blue")
                table.add_column("Completion Rate", style="yellow")
                
                for agent_name, agent_stats in stats['agent_statistics'].items():
                    table.add_row(
                        agent_name,
                        str(agent_stats['total_tasks']),
                        str(agent_stats['completed_tasks']),
                        f"{agent_stats['completion_rate']:.1%}"
                    )
                
                console.print(table)
                
        except Exception as e:
            rprint(f"❌ [red]Error accessing memory: {e}[/red]")
    
    asyncio.run(show_memory())


@cli.command()
@click.pass_context
def examples(ctx):
    """Show example workflows and tasks."""
    rprint(Panel.fit(
        "📚 Example Workflows\n\n"
        "1. Code Analysis Workflow:\n"
        "   - Submit code to software_architect for review\n"
        "   - Get recommendations from tech_lead\n"
        "   - Implement changes with python_expert\n\n"
        "2. Research Workflow:\n"
        "   - Query active_inference_expert for theory\n"
        "   - Get implementation guidance from python_expert\n"
        "   - Coordinate with orchestrator\n\n"
        "3. Multi-Agent Task:\n"
        "   - Submit complex task to orchestrator\n"
        "   - Orchestrator delegates to appropriate agents\n"
        "   - Results aggregated and synthesized",
        title="Example Workflows"
    ))
    
    # Example task files
    examples_dir = Path(__file__).parent.parent / "examples"
    if examples_dir.exists():
        rprint("\n📁 Example task files:")
        for example_file in examples_dir.glob("*.json"):
            rprint(f"   • {example_file.name}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()