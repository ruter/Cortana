"""
Tests for Skills System

The skills system allows creating custom CLI tools with SKILL.md files.
Ported from badlogic/pi-mono mom package.
"""

import os
import tempfile
import pytest

# Import the skills module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from skills import (
    Skill,
    parse_frontmatter,
    load_skill_from_file,
    load_skills_from_dir,
    load_all_skills,
    format_skills_for_prompt,
    get_skill_content,
    create_skill_template
)


# --- Frontmatter Parsing Tests ---

class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""
    
    def test_valid_frontmatter(self):
        """Test parsing valid frontmatter."""
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

This is the content.
"""
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter is not None
        assert frontmatter['name'] == 'test-skill'
        assert frontmatter['description'] == 'A test skill'
        assert '# Test Skill' in body
    
    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "# Just a heading\n\nSome content."
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter is None
        assert body == content
    
    def test_incomplete_frontmatter(self):
        """Test content with incomplete frontmatter (no closing delimiter)."""
        content = """---
name: test
description: incomplete
# Missing closing ---

Content here.
"""
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter is None
        assert body == content
    
    def test_empty_frontmatter(self):
        """Test content with empty frontmatter."""
        content = """---
---

Content only.
"""
        frontmatter, body = parse_frontmatter(content)
        
        # Empty YAML parses to None
        assert frontmatter is None or frontmatter == {}


# --- Skill Loading Tests ---

class TestLoadSkillFromFile:
    """Tests for loading individual skills from SKILL.md files."""
    
    @pytest.fixture
    def skill_dir(self):
        """Create a temporary skill directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'test-skill')
            os.makedirs(skill_path)
            
            skill_md = os.path.join(skill_path, 'SKILL.md')
            with open(skill_md, 'w') as f:
                f.write("""---
name: test-skill
description: A test skill for testing
---

# Test Skill

Usage instructions here.
""")
            yield skill_md
    
    def test_load_valid_skill(self, skill_dir):
        """Test loading a valid skill."""
        skill = load_skill_from_file(skill_dir, 'global')
        
        assert skill is not None
        assert skill.name == 'test-skill'
        assert skill.description == 'A test skill for testing'
        assert skill.source == 'global'
        assert skill.file_path == skill_dir
    
    def test_load_skill_missing_name(self):
        """Test loading a skill without a name field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, 'SKILL.md')
            with open(skill_md, 'w') as f:
                f.write("""---
description: No name field
---

Content.
""")
            skill = load_skill_from_file(skill_md, 'global')
            assert skill is None
    
    def test_load_skill_no_frontmatter(self):
        """Test loading a skill without frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = os.path.join(tmpdir, 'SKILL.md')
            with open(skill_md, 'w') as f:
                f.write("# Just content, no frontmatter\n")
            
            skill = load_skill_from_file(skill_md, 'global')
            assert skill is None
    
    def test_load_nonexistent_file(self):
        """Test loading from a nonexistent file."""
        skill = load_skill_from_file('/nonexistent/SKILL.md', 'global')
        assert skill is None


# --- Directory Loading Tests ---

class TestLoadSkillsFromDir:
    """Tests for loading skills from a directory."""
    
    @pytest.fixture
    def skills_dir(self):
        """Create a temporary skills directory with multiple skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create skill 1
            skill1_path = os.path.join(tmpdir, 'skill-one')
            os.makedirs(skill1_path)
            with open(os.path.join(skill1_path, 'SKILL.md'), 'w') as f:
                f.write("""---
name: skill-one
description: First skill
---

# Skill One
""")
            
            # Create skill 2
            skill2_path = os.path.join(tmpdir, 'skill-two')
            os.makedirs(skill2_path)
            with open(os.path.join(skill2_path, 'SKILL.md'), 'w') as f:
                f.write("""---
name: skill-two
description: Second skill
---

# Skill Two
""")
            
            # Create a directory without SKILL.md (should be ignored)
            os.makedirs(os.path.join(tmpdir, 'not-a-skill'))
            
            yield tmpdir
    
    def test_load_multiple_skills(self, skills_dir):
        """Test loading multiple skills from a directory."""
        skills = load_skills_from_dir(skills_dir, 'global')
        
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert 'skill-one' in names
        assert 'skill-two' in names
    
    def test_load_from_empty_dir(self):
        """Test loading from an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = load_skills_from_dir(tmpdir, 'global')
            assert skills == []
    
    def test_load_from_nonexistent_dir(self):
        """Test loading from a nonexistent directory."""
        skills = load_skills_from_dir('/nonexistent/dir', 'global')
        assert skills == []


# --- Load All Skills Tests ---

class TestLoadAllSkills:
    """Tests for loading all skills (global and user-specific)."""
    
    @pytest.fixture
    def workspace(self):
        """Create a workspace with global and user skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create global skills directory
            global_skills = os.path.join(tmpdir, 'skills')
            os.makedirs(global_skills)
            
            # Create global skill
            global_skill_path = os.path.join(global_skills, 'global-skill')
            os.makedirs(global_skill_path)
            with open(os.path.join(global_skill_path, 'SKILL.md'), 'w') as f:
                f.write("""---
name: global-skill
description: A global skill
---

# Global Skill
""")
            
            # Create user skills directory
            user_skills = os.path.join(tmpdir, 'users', '12345', 'skills')
            os.makedirs(user_skills)
            
            # Create user skill
            user_skill_path = os.path.join(user_skills, 'user-skill')
            os.makedirs(user_skill_path)
            with open(os.path.join(user_skill_path, 'SKILL.md'), 'w') as f:
                f.write("""---
name: user-skill
description: A user-specific skill
---

# User Skill
""")
            
            yield tmpdir
    
    def test_load_global_only(self, workspace):
        """Test loading only global skills (no user_id)."""
        skills = load_all_skills(workspace)
        
        assert len(skills) == 1
        assert skills[0].name == 'global-skill'
        assert skills[0].source == 'global'
    
    def test_load_global_and_user(self, workspace):
        """Test loading both global and user skills."""
        skills = load_all_skills(workspace, user_id='12345')
        
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert 'global-skill' in names
        assert 'user-skill' in names
    
    def test_user_skill_overrides_global(self):
        """Test that user skills override global skills with same name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create global skill
            global_skills = os.path.join(tmpdir, 'skills', 'same-name')
            os.makedirs(global_skills)
            with open(os.path.join(global_skills, 'SKILL.md'), 'w') as f:
                f.write("""---
name: same-name
description: Global version
---
""")
            
            # Create user skill with same name
            user_skills = os.path.join(tmpdir, 'users', '12345', 'skills', 'same-name')
            os.makedirs(user_skills)
            with open(os.path.join(user_skills, 'SKILL.md'), 'w') as f:
                f.write("""---
name: same-name
description: User version
---
""")
            
            skills = load_all_skills(tmpdir, user_id='12345')
            
            assert len(skills) == 1
            assert skills[0].name == 'same-name'
            assert skills[0].description == 'User version'
            assert skills[0].source == 'user'


# --- Formatting Tests ---

class TestFormatSkillsForPrompt:
    """Tests for formatting skills for system prompt."""
    
    def test_format_empty_list(self):
        """Test formatting an empty skills list."""
        result = format_skills_for_prompt([])
        assert "no skills" in result.lower()
    
    def test_format_single_skill(self):
        """Test formatting a single skill."""
        skill = Skill(
            name='test-skill',
            description='A test skill',
            file_path='/workspace/skills/test-skill/SKILL.md',
            base_dir='/workspace/skills/test-skill',
            source='global'
        )
        result = format_skills_for_prompt([skill])
        
        assert 'test-skill' in result
        assert 'A test skill' in result
        assert '[global]' in result
    
    def test_format_multiple_skills_sorted(self):
        """Test that skills are sorted by name."""
        skills = [
            Skill(name='zebra', description='Z skill', file_path='/z', base_dir='/z', source='global'),
            Skill(name='alpha', description='A skill', file_path='/a', base_dir='/a', source='user'),
        ]
        result = format_skills_for_prompt(skills)
        
        # Alpha should come before zebra
        alpha_pos = result.find('alpha')
        zebra_pos = result.find('zebra')
        assert alpha_pos < zebra_pos


# --- Skill Content Tests ---

class TestGetSkillContent:
    """Tests for reading skill content."""
    
    def test_get_content_with_placeholder(self):
        """Test that {baseDir} placeholder is replaced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, 'test-skill')
            os.makedirs(skill_path)
            
            skill_md = os.path.join(skill_path, 'SKILL.md')
            with open(skill_md, 'w') as f:
                f.write("""---
name: test-skill
description: Test
---

Scripts are in: {baseDir}/scripts/
""")
            
            skill = Skill(
                name='test-skill',
                description='Test',
                file_path=skill_md,
                base_dir=skill_path,
                source='global'
            )
            
            content = get_skill_content(skill)
            
            assert content is not None
            assert '{baseDir}' not in content
            assert skill_path in content


# --- Template Generation Tests ---

class TestCreateSkillTemplate:
    """Tests for skill template generation."""
    
    def test_create_template(self):
        """Test creating a skill template."""
        template = create_skill_template('my-skill', 'Does something useful')
        
        assert 'name: my-skill' in template
        assert 'description: Does something useful' in template
        assert '# My Skill' in template  # Title case conversion
        assert '{baseDir}' in template  # Placeholder for scripts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
