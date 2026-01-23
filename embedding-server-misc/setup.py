"""Setup configuration for embedding-server-misc."""
from setuptools import setup, find_packages

setup(
    name="embedding-server-misc",
    version="1.0.0",
    description="Local embedding server using llama.cpp (CPU optimized)",
    author="artqcid",
    url="https://github.com/artqcid/embedding-server-misc",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "llama-cpp-python>=0.2.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
    entry_points={
        "console_scripts": [
            "embedding-server=embedding_server.__main__:main",
        ],
    },
)
