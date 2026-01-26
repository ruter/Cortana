"""
Skills System for Cortana

Ported from badlogic/pi-mono mom package.

Skills are custom CLI tools that the agent can create and use for recurring tasks.
Each skill is a directory containing a SKILL.md file with YAML frontmatter
describing the skill, plus any scripts or programs needed to use the skill.

Directory Structure:
    /workspace/skills/           # Global skills (shared across all users)
        skill-name/
            SKILL.md             # Skill definition with frontmatter
            script.py            # Implementation scripts
            ...
    /workspace/users/{user_id}/skills/   # User-specific skills
        skill-name/
            SKILL.md
            ...

SKILL.md Format:
    ---
    name: skill-name
    description: Short description of what this skill does
    ---

    # Skill Name

    Usage instructions, examples, etc.
    Scripts are in: {baseDir}/
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import yaml


@dataclass
class Skill:
    """Represents a loaded skill."""
    name: str
    description: str
    file_path: str      # Path to SKILL.md
    base_dir: str       # Directory containing the skill
    source: str         # "global" or "user"


@dataclass
class SkillFrontmatter:
    """Parsed SKILL.md frontmatter."""
    name: str
    description: str


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """
    Parse YAML frontmatter from markdown content.
    
    Args:
        content: Full markdown content with optional frontmatter.
    
    Returns:
        Tuple of (frontmatter_dict or None, remaining_content)
    """
    # Check for frontmatter delimiter
    if not content.startswith('---'):
        return None, content
    
    # Find the closing delimiter
    lines = content.split('\n')
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end_idx = i
            break
    
    if end_idx is None:
        return None, content
    
    # Parse YAML frontmatter
    frontmatter_text = '\n'.join(lines[1:end_idx])
    remaining_content = '\n'.join(lines[end_idx + 1:])
    
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter, remaining_content.strip()
    except yaml.YAMLError:
        return None, content


def load_skill_from_file(skill_md_path: str, source: str) -> Optional[Skill]:
    """
    Load a skill from a SKILL.md file.
    
    Args:
        skill_md_path: Path to the SKILL.md file.
        source: Source identifier ("global" or "user").
    
    Returns:
        Skill object if valid, None otherwise.
    """
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, _ = parse_frontmatter(content)
        
        if not frontmatter:
            return None
        
        name = frontmatter.get('name')
        description = frontmatter.get('description', '')
        
        if not name:
            return None
        
        base_dir = os.path.dirname(skill_md_path)
        
        return Skill(
            name=name,
            description=description,
            file_path=skill_md_path,
            base_dir=base_dir,
            source=source
        )
        
    except Exception as e:
        print(f"Error loading skill from {skill_md_path}: {e}")
        return None


def load_skills_from_dir(directory: str, source: str) -> List[Skill]:
    """
    Load all skills from a directory.
    
    Scans for subdirectories containing SKILL.md files.
    
    Args:
        directory: Directory to scan for skills.
        source: Source identifier for loaded skills.
    
    Returns:
        List of loaded Skill objects.
    """
    skills = []
    
    if not os.path.isdir(directory):
        return skills
    
    # Scan for skill directories
    try:
        for entry in os.scandir(directory):
            if entry.is_dir():
                skill_md_path = os.path.join(entry.path, 'SKILL.md')
                if os.path.isfile(skill_md_path):
                    skill = load_skill_from_file(skill_md_path, source)
                    if skill:
                        skills.append(skill)
    except Exception as e:
        print(f"Error scanning skills directory {directory}: {e}")
    
    return skills


def load_all_skills(workspace_dir: str, user_id: Optional[str] = None) -> List[Skill]:
    """
    Load all available skills (global and user-specific).
    
    User-specific skills override global skills with the same name.
    
    Args:
        workspace_dir: Base workspace directory.
        user_id: Optional user ID for loading user-specific skills.
    
    Returns:
        List of all available skills (deduplicated by name).
    """
    skill_map = {}
    
    # Load global skills first
    global_skills_dir = os.path.join(workspace_dir, 'skills')
    for skill in load_skills_from_dir(global_skills_dir, 'global'):
        skill_map[skill.name] = skill
    
    # Load user-specific skills (override global on collision)
    if user_id:
        user_skills_dir = os.path.join(workspace_dir, 'users', str(user_id), 'skills')
        for skill in load_skills_from_dir(user_skills_dir, 'user'):
            skill_map[skill.name] = skill
    
    return list(skill_map.values())


def format_skills_for_prompt(skills: List[Skill]) -> str:
    """
    Format skills list for system prompt injection.
    
    Args:
        skills: List of skills to format.
    
    Returns:
        Formatted string listing available skills.
    """
    if not skills:
        return "(no skills installed yet)"
    
    lines = []
    for skill in sorted(skills, key=lambda s: s.name):
        source_tag = f"[{skill.source}]" if skill.source else ""
        lines.append(f"- **{skill.name}** {source_tag}: {skill.description}")
        lines.append(f"  Location: `{skill.file_path}`")
    
    return '\n'.join(lines)


def get_skill_content(skill: Skill) -> Optional[str]:
    """
    Read the full content of a skill's SKILL.md file.
    
    Args:
        skill: Skill object to read.
    
    Returns:
        Full SKILL.md content, or None if read fails.
    """
    try:
        with open(skill.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace {baseDir} placeholder with actual path
        content = content.replace('{baseDir}', skill.base_dir)
        
        return content
    except Exception as e:
        print(f"Error reading skill content from {skill.file_path}: {e}")
        return None


def create_skill_template(name: str, description: str) -> str:
    """
    Generate a template SKILL.md content for a new skill.
    
    Args:
        name: Skill name.
        description: Short description.
    
    Returns:
        Template SKILL.md content.
    """
    return f"""---
name: {name}
description: {description}
---

# {name.replace('-', ' ').title()}

{description}

## Usage

```bash
# Example usage
bash {{baseDir}}/script.sh [arguments]
```

## Files

- `script.sh` - Main script (create this file)

## Notes

Add any additional notes or documentation here.
"""
