"""
Tests for Coding Tools (bash, read_file, write_file, edit_file)

These tools are ported from badlogic/pi-mono mom package.
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Import the tools module
from src.tools import (
    execute_bash,
    read_file,
    write_file,
    edit_file,
    _truncate_output,
    _format_size
)


# --- Helper Functions Tests ---

class TestTruncateOutput:
    """Tests for the _truncate_output helper function."""
    
    def test_no_truncation_needed(self):
        """Test that short output is not truncated."""
        output = "line1\nline2\nline3"
        result, was_truncated, info = _truncate_output(output)
        assert result == output
        assert was_truncated is False
        assert info == {}
    
    def test_empty_output(self):
        """Test handling of empty output."""
        result, was_truncated, info = _truncate_output("")
        assert result == ""
        assert was_truncated is False
    
    def test_truncate_by_lines(self):
        """Test truncation by line count."""
        lines = [f"line{i}" for i in range(1000)]
        output = "\n".join(lines)
        result, was_truncated, info = _truncate_output(output, max_lines=100)
        
        assert was_truncated is True
        assert info['total_lines'] == 1000
        assert info['output_lines'] == 100
        assert "line999" in result  # Should keep the tail
        assert "line0" not in result  # Should truncate the head
    
    def test_truncate_by_bytes(self):
        """Test truncation by byte count."""
        # Create output larger than 1KB
        output = "x" * 2000
        result, was_truncated, info = _truncate_output(output, max_bytes=1000)
        
        assert was_truncated is True
        assert len(result.encode('utf-8')) <= 1000


class TestFormatSize:
    """Tests for the _format_size helper function."""
    
    def test_bytes(self):
        assert _format_size(500) == "500B"
    
    def test_kilobytes(self):
        assert _format_size(2048) == "2.0KB"
    
    def test_megabytes(self):
        assert _format_size(2 * 1024 * 1024) == "2.0MB"


# --- Execute Bash Tests ---

class TestExecuteBash:
    """Tests for the execute_bash tool."""
    
    @pytest.fixture
    def mock_ctx(self):
        """Create a mock RunContext."""
        ctx = MagicMock()
        ctx.deps = {'user_info': {'id': 12345, 'name': 'TestUser'}}
        return ctx
    
    @pytest.mark.asyncio
    async def test_simple_command(self, mock_ctx):
        """Test executing a simple echo command."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.BASH_TIMEOUT_DEFAULT = 60
            
            result = await execute_bash(mock_ctx, "echo 'hello world'")
            assert "hello world" in result
    
    @pytest.mark.asyncio
    async def test_command_with_exit_code(self, mock_ctx):
        """Test that non-zero exit codes are reported."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.BASH_TIMEOUT_DEFAULT = 60
            
            result = await execute_bash(mock_ctx, "exit 1")
            assert "exited with code 1" in result
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, mock_ctx):
        """Test that commands timeout correctly."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.BASH_TIMEOUT_DEFAULT = 60
            
            result = await execute_bash(mock_ctx, "sleep 10", timeout=1)
            assert "timed out" in result
    
    @pytest.mark.asyncio
    async def test_command_with_stderr(self, mock_ctx):
        """Test that stderr is captured."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.BASH_TIMEOUT_DEFAULT = 60
            
            result = await execute_bash(mock_ctx, "echo 'error' >&2")
            assert "error" in result


# --- Read File Tests ---

class TestReadFile:
    """Tests for the read_file tool."""
    
    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.deps = {'user_info': {'id': 12345, 'name': 'TestUser'}}
        return ctx
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i in range(1, 11):
                f.write(f"Line {i}\n")
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_read_entire_file(self, mock_ctx, temp_file):
        """Test reading an entire file."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.FILE_READ_MAX_LINES = 1000
            
            result = await read_file(mock_ctx, temp_file)
            assert "Line 1" in result
            assert "Line 10" in result
    
    @pytest.mark.asyncio
    async def test_read_with_offset(self, mock_ctx, temp_file):
        """Test reading with line offset."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.FILE_READ_MAX_LINES = 1000
            
            result = await read_file(mock_ctx, temp_file, offset=5)
            assert "Line 5" in result
            assert "Line 1" not in result or "Line 10" in result
    
    @pytest.mark.asyncio
    async def test_read_with_limit(self, mock_ctx, temp_file):
        """Test reading with line limit."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            mock_config.FILE_READ_MAX_LINES = 1000
            
            result = await read_file(mock_ctx, temp_file, offset=1, limit=3)
            assert "Line 1" in result
            assert "Line 3" in result
            # Line 4 should not be in the result (only 3 lines requested)
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, mock_ctx):
        """Test reading a file that doesn't exist."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            
            result = await read_file(mock_ctx, "/nonexistent/file.txt")
            assert "Error" in result or "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_read_empty_file(self, mock_ctx):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.flush()
            temp_path = f.name
        
        try:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = '/tmp'
                mock_config.FILE_READ_MAX_LINES = 1000
                
                result = await read_file(mock_ctx, temp_path)
                assert "empty" in result.lower()
        finally:
            os.unlink(temp_path)


# --- Write File Tests ---

class TestWriteFile:
    """Tests for the write_file tool."""
    
    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.deps = {'user_info': {'id': 12345, 'name': 'TestUser'}}
        return ctx
    
    @pytest.mark.asyncio
    async def test_write_new_file(self, mock_ctx):
        """Test writing a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "test.txt")
                result = await write_file(mock_ctx, test_path, "Hello, World!")
                
                assert "written" in result.lower()
                assert os.path.exists(test_path)
                with open(test_path, 'r') as f:
                    assert f.read() == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_write_creates_directories(self, mock_ctx):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "nested", "dir", "test.txt")
                result = await write_file(mock_ctx, test_path, "Content")
                
                assert "written" in result.lower()
                assert os.path.exists(test_path)
    
    @pytest.mark.asyncio
    async def test_write_overwrites_existing(self, mock_ctx):
        """Test that existing files are overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "test.txt")
                
                # Write initial content
                with open(test_path, 'w') as f:
                    f.write("Original content")
                
                # Overwrite
                result = await write_file(mock_ctx, test_path, "New content")
                
                assert "written" in result.lower()
                with open(test_path, 'r') as f:
                    assert f.read() == "New content"


# --- Edit File Tests ---

class TestEditFile:
    """Tests for the edit_file tool."""
    
    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.deps = {'user_info': {'id': 12345, 'name': 'TestUser'}}
        return ctx
    
    @pytest.mark.asyncio
    async def test_edit_simple_replacement(self, mock_ctx):
        """Test simple text replacement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "test.txt")
                with open(test_path, 'w') as f:
                    f.write("Hello, World!")
                
                result = await edit_file(mock_ctx, test_path, "World", "Universe")
                
                assert "edited" in result.lower()
                with open(test_path, 'r') as f:
                    assert f.read() == "Hello, Universe!"
    
    @pytest.mark.asyncio
    async def test_edit_text_not_found(self, mock_ctx):
        """Test error when text to replace is not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "test.txt")
                with open(test_path, 'w') as f:
                    f.write("Hello, World!")
                
                result = await edit_file(mock_ctx, test_path, "Goodbye", "Hi")
                
                assert "error" in result.lower() or "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_edit_multiple_occurrences(self, mock_ctx):
        """Test that all occurrences are replaced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                
                test_path = os.path.join(tmpdir, "test.txt")
                with open(test_path, 'w') as f:
                    f.write("foo bar foo baz foo")
                
                result = await edit_file(mock_ctx, test_path, "foo", "qux")
                
                assert "3 occurrence" in result.lower()
                with open(test_path, 'r') as f:
                    content = f.read()
                    assert content == "qux bar qux baz qux"
    
    @pytest.mark.asyncio
    async def test_edit_nonexistent_file(self, mock_ctx):
        """Test editing a file that doesn't exist."""
        with patch('src.tools.config') as mock_config:
            mock_config.WORKSPACE_DIR = '/tmp'
            
            result = await edit_file(mock_ctx, "/nonexistent/file.txt", "old", "new")
            assert "error" in result.lower() or "not found" in result.lower()


# --- Integration Tests ---

class TestCodingToolsIntegration:
    """Integration tests for coding tools working together."""
    
    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.deps = {'user_info': {'id': 12345, 'name': 'TestUser'}}
        return ctx
    
    @pytest.mark.asyncio
    async def test_write_then_read(self, mock_ctx):
        """Test writing a file then reading it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                mock_config.FILE_READ_MAX_LINES = 1000
                
                test_path = os.path.join(tmpdir, "test.txt")
                content = "Line 1\nLine 2\nLine 3"
                
                # Write
                write_result = await write_file(mock_ctx, test_path, content)
                assert "written" in write_result.lower()
                
                # Read
                read_result = await read_file(mock_ctx, test_path)
                assert "Line 1" in read_result
                assert "Line 2" in read_result
                assert "Line 3" in read_result
    
    @pytest.mark.asyncio
    async def test_write_edit_read(self, mock_ctx):
        """Test write -> edit -> read workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.tools.config') as mock_config:
                mock_config.WORKSPACE_DIR = tmpdir
                mock_config.FILE_READ_MAX_LINES = 1000
                
                test_path = os.path.join(tmpdir, "test.txt")
                
                # Write initial content
                await write_file(mock_ctx, test_path, "Hello, World!")
                
                # Edit
                await edit_file(mock_ctx, test_path, "World", "Cortana")
                
                # Read and verify
                read_result = await read_file(mock_ctx, test_path)
                assert "Cortana" in read_result
                assert "World" not in read_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
