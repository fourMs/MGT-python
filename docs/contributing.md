# Contributing to MGT-python

We welcome contributions to the Musical Gestures Toolbox for Python! This guide will help you get started with contributing to the project.

## Getting Started

### Fork and Clone

1. **Fork** the repository on GitHub: [https://github.com/fourMs/MGT-python](https://github.com/fourMs/MGT-python)

2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MGT-python.git
   cd MGT-python
   ```

3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/fourMs/MGT-python.git
   ```

### Development Environment

#### Set up virtual environment
```bash
# Create virtual environment
python -m venv mgt-dev
source mgt-dev/bin/activate  # Linux/macOS
# mgt-dev\Scripts\activate   # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Development Dependencies
```bash
# Testing
pip install pytest pytest-cov

# Code quality
pip install black flake8 isort mypy

# Documentation
pip install mkdocs mkdocs-material mkdocstrings[python]

# Optional: Jupyter for notebook development
pip install jupyter notebook
```

## Development Workflow

### 1. Create a Feature Branch

Always work on a feature branch, never directly on master:

```bash
git checkout master
git pull upstream master
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow the coding standards and patterns established in the codebase:

#### Code Style Guidelines

- **PEP 8** compliance for Python code
- **4 spaces** for indentation (no tabs)
- **Line length**: Maximum 88 characters (Black default)
- **Imports**: Group and sort imports using isort
- **Docstrings**: Use Google-style docstrings

#### Example Function Documentation

```python
def mg_example_function(video_path, param1=None, param2=False):
    """
    Brief description of the function.
    
    Longer description explaining what the function does,
    how it works, and any important details.
    
    Args:
        video_path (str): Path to the input video file.
        param1 (int, optional): Description of param1. Defaults to None.
        param2 (bool, optional): Description of param2. Defaults to False.
        
    Returns:
        dict: Dictionary containing:
            - 'output_path': Path to generated output file
            - 'data': Processed data array
            
    Raises:
        FileNotFoundError: If video_path does not exist.
        ValueError: If param1 is negative.
        
    Example:
        >>> result = mg_example_function('video.mp4', param1=10)
        >>> print(result['output_path'])
        'video_processed.mp4'
    """
    # Implementation here
    pass
```

### 3. Code Quality Checks

Before committing, run these checks:

#### Formatting
```bash
# Format code with Black
black musicalgestures/

# Sort imports
isort musicalgestures/

# Check formatting
black --check musicalgestures/
isort --check-only musicalgestures/
```

#### Linting
```bash
# Check code style
flake8 musicalgestures/

# Type checking (optional but recommended)
mypy musicalgestures/
```

#### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=musicalgestures tests/

# Run specific test file
pytest tests/test_video.py

# Run specific test
pytest tests/test_video.py::test_video_loading
```

### 4. Add Tests

All new functionality should include tests. Add tests to the appropriate file in the `tests/` directory:

#### Test Structure
```python
import pytest
import musicalgestures as mg
from pathlib import Path


class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        # Arrange
        video_path = mg.examples.dance
        
        # Act
        result = mg.new_feature(video_path)
        
        # Assert
        assert result is not None
        assert Path(result['output_path']).exists()
    
    def test_error_handling(self):
        """Test that errors are handled appropriately."""
        with pytest.raises(FileNotFoundError):
            mg.new_feature('nonexistent_file.mp4')
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        video_path = mg.examples.dance
        
        # Test invalid parameter
        with pytest.raises(ValueError):
            mg.new_feature(video_path, invalid_param=-1)
```

### 5. Update Documentation

#### Docstrings
Ensure all new functions and classes have proper docstrings following the Google style.

#### User Documentation
If adding user-facing features, update the relevant documentation files:

- `docs/user-guide/` - User guide sections
- `docs/examples.md` - Add usage examples
- `docs/api-reference/` - API documentation (auto-generated from docstrings)

#### Changelog
Add entry to `CHANGELOG.md` (if it exists) or prepare release notes.

### 6. Commit Your Changes

#### Commit Message Format
Use clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "Add optical flow visualization method"
git commit -m "Fix memory leak in video processing"
git commit -m "Update documentation for audio analysis"

# Include issue references when applicable
git commit -m "Fix video loading issue (#123)"
```

#### Commit Best Practices
- Make **atomic commits** (one logical change per commit)
- Write **descriptive commit messages**
- **Reference issues** in commit messages when applicable

## Types of Contributions

### Bug Fixes

1. **Check existing issues** - Make sure the bug hasn't been reported
2. **Create an issue** if one doesn't exist
3. **Fix the bug** and add a test to prevent regression
4. **Reference the issue** in your pull request

### New Features

1. **Discuss the feature** by creating an issue first
2. **Follow existing patterns** in the codebase
3. **Add comprehensive tests**
4. **Update documentation**
5. **Consider backward compatibility**

### Documentation Improvements

- Fix typos and grammatical errors
- Improve existing documentation clarity
- Add missing documentation
- Create new examples and tutorials
- Improve code comments

### Examples and Tutorials

- Create Jupyter notebooks demonstrating features
- Add real-world use cases
- Improve existing examples
- Add visualizations and plots

## Pull Request Process

### 1. Prepare Your Pull Request

Before creating a PR:

```bash
# Sync with upstream
git checkout master
git pull upstream master

# Rebase your feature branch
git checkout feature/your-feature-name
git rebase master

# Run all checks
black musicalgestures/
isort musicalgestures/
flake8 musicalgestures/
pytest
```

### 2. Create Pull Request

- **Title**: Clear, descriptive title
- **Description**: Explain what changes were made and why
- **Testing**: Describe how the changes were tested
- **Documentation**: Note any documentation updates
- **Issues**: Reference any related issues

#### PR Template Example
```markdown
## Description
Brief description of changes made.

## Changes Made
- Added new feature X
- Fixed bug Y  
- Updated documentation Z

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Tested manually with sample videos

## Documentation
- [ ] Updated docstrings
- [ ] Updated user guide
- [ ] Added examples

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
```

### 3. Review Process

- **Automated checks** must pass (CI/CD)
- **Code review** by maintainers
- **Address feedback** promptly
- **Update PR** as needed

## Code Organization

### File Structure
```
musicalgestures/
├── __init__.py              # Package initialization
├── _video.py               # Video processing (MgVideo class)
├── _audio.py               # Audio processing (MgAudio class)
├── _flow.py                # Optical flow analysis
├── _utils.py               # Utility functions
├── _motionvideo.py         # Motion video creation
├── _motiongrams.py         # Motiongram generation
└── ...                     # Other specialized modules
```

### Naming Conventions

- **Files**: Use underscore prefix for internal modules (`_video.py`)
- **Classes**: PascalCase (`MgVideo`, `MgAudio`)
- **Functions**: snake_case (`mg_motion_video`, `create_motiongram`)
- **Variables**: snake_case (`frame_count`, `output_path`)
- **Constants**: UPPER_CASE (`DEFAULT_THRESHOLD`, `MAX_FRAMES`)

## Testing Guidelines

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test with large files (optional)

### Test Data

Use the built-in example videos for consistency:
```python
import musicalgestures as mg

# Use example videos in tests
video_path = mg.examples.dance
audio_path = mg.examples.pianist
```

### Mocking External Dependencies

For tests that don't require actual video processing:
```python
from unittest.mock import patch, MagicMock

@patch('musicalgestures._video.cv2.VideoCapture')
def test_video_loading(mock_cv2):
    # Mock OpenCV video capture
    mock_cap = MagicMock()
    mock_cv2.return_value = mock_cap
    
    # Test the functionality
    mv = mg.MgVideo('fake_video.mp4')
    # Assert expected behavior
```

## Release Process

### Version Numbering

MGT-python follows semantic versioning (SemVer):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

### Release Checklist

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release tag
4. Build and upload to PyPI
5. Update documentation

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: a.r.jensenius@imv.uio.no (maintainer)

### Resources

- **fourMs Lab**: [https://github.com/fourMs](https://github.com/fourMs)
- **RITMO Centre**: [https://www.uio.no/ritmo/english/](https://www.uio.no/ritmo/english/)
- **Documentation**: [https://mgt-python.readthedocs.io/](https://mgt-python.readthedocs.io/)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards
- Credit others for their contributions

Thank you for contributing to MGT-python! 🎵🎥
