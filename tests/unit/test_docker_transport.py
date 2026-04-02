"""Unit tests for Docker transport configuration and command building."""

import pytest

from haive.mcp.client.transport import DockerTransport
from haive.mcp.config import MCPServerConfig, MCPTransport


class TestDockerTransportConfig:
    """Test Docker transport configuration and command building."""

    def test_docker_transport_enum_exists(self):
        """Docker transport type is available in MCPTransport enum."""
        assert MCPTransport.DOCKER == "docker"
        assert MCPTransport.DOCKER.value == "docker"

    def test_server_config_with_docker_transport(self):
        """MCPServerConfig accepts docker transport and docker-specific fields."""
        config = MCPServerConfig(
            name="test-postgres",
            transport=MCPTransport.DOCKER,
            command="mcp/postgres",
            env={"POSTGRES_HOST": "localhost"},
            docker_volumes=["/data:/data:ro"],
            docker_ports=["5432:5432"],
            docker_network="host",
        )
        assert config.transport == MCPTransport.DOCKER
        assert config.command == "mcp/postgres"
        assert config.docker_volumes == ["/data:/data:ro"]
        assert config.docker_ports == ["5432:5432"]
        assert config.docker_network == "host"

    def test_server_config_docker_defaults(self):
        """Docker-specific fields default to empty when not provided."""
        config = MCPServerConfig(
            name="test",
            transport=MCPTransport.STDIO,
        )
        assert config.docker_volumes == []
        assert config.docker_ports == []
        assert config.docker_network is None

    def test_docker_transport_basic_command(self):
        """DockerTransport builds a basic docker run command."""
        transport = DockerTransport(image="mcp/filesystem")
        cmd = transport._build_docker_command()
        assert cmd == ["docker", "run", "--rm", "-i", "mcp/filesystem"]

    def test_docker_transport_with_env(self):
        """DockerTransport passes environment variables correctly."""
        transport = DockerTransport(
            image="mcp/postgres",
            env={"DB_HOST": "localhost", "DB_PORT": "5432"},
        )
        cmd = transport._build_docker_command()
        assert "-e" in cmd
        assert "DB_HOST=localhost" in cmd
        assert "DB_PORT=5432" in cmd

    def test_docker_transport_with_volumes(self):
        """DockerTransport adds volume mounts."""
        transport = DockerTransport(
            image="mcp/filesystem",
            volumes=["/host/data:/data:ro", "/host/config:/config"],
        )
        cmd = transport._build_docker_command()
        assert cmd.count("-v") == 2
        assert "/host/data:/data:ro" in cmd
        assert "/host/config:/config" in cmd

    def test_docker_transport_with_ports(self):
        """DockerTransport adds port mappings."""
        transport = DockerTransport(
            image="mcp/server",
            ports=["8080:8080", "9090:9090"],
        )
        cmd = transport._build_docker_command()
        assert cmd.count("-p") == 2
        assert "8080:8080" in cmd

    def test_docker_transport_with_network(self):
        """DockerTransport sets Docker network."""
        transport = DockerTransport(
            image="mcp/server",
            network="host",
        )
        cmd = transport._build_docker_command()
        assert "--network" in cmd
        assert "host" in cmd

    def test_docker_transport_with_extra_args(self):
        """DockerTransport passes extra docker run arguments."""
        transport = DockerTransport(
            image="mcp/server",
            docker_args=["--cpus", "2", "--memory", "512m"],
        )
        cmd = transport._build_docker_command()
        assert "--cpus" in cmd
        assert "2" in cmd
        assert "--memory" in cmd
        assert "512m" in cmd

    def test_docker_transport_full_command(self):
        """DockerTransport builds a complete command with all options."""
        transport = DockerTransport(
            image="mcp/postgres:latest",
            env={"POSTGRES_DB": "mydb"},
            volumes=["/data:/data"],
            ports=["5432:5432"],
            network="bridge",
            docker_args=["--name", "mcp-postgres"],
        )
        cmd = transport._build_docker_command()

        # Verify order: docker run --rm -i [options] image
        assert cmd[0] == "docker"
        assert cmd[1] == "run"
        assert cmd[-1] == "mcp/postgres:latest"
        assert "-e" in cmd
        assert "-v" in cmd
        assert "-p" in cmd
        assert "--network" in cmd

    def test_docker_transport_not_connected_initially(self):
        """DockerTransport starts in disconnected state."""
        transport = DockerTransport(image="mcp/test")
        assert not transport.connected
        assert transport.process is None
