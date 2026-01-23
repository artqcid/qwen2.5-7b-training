"""Setup configuration for mcp-server-misc."""
from setuptools import setup, find_packages

setup(
    name="mcp-server-misc",
    version="1.0.0",
    description="Generalized MCP server for web documentation context",
    author="artqcid",
    author_email="markus.wagner.devblogs@gmail.com",
    url="https://github.com/artqcid/mcp-server-misc",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "mcp>=0.1.0",
        "httpx>=0.25.0",
        "beautifulsoup4>=4.12.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
    entry_points={
        "console_scripts": [
            "mcp-server=mcp_server.__main__:main",
        ],
    },
)
