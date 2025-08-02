# Testing Guide

This guide covers how to run and write tests for MGT-python, ensuring code quality and reliability.

## Running Tests

### Prerequisites

Make sure you have the development dependencies installed:

```bash
pip install pytest pytest-cov
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_video.py

# Run specific test method
pytest tests/test_video.py::TestMgVideo::test_video_loading

# Run tests matching a pattern
pytest -k "test_motion"
```

### Test Coverage

```bash
# Run tests with coverage report
pytest --cov=musicalgestures

# Generate HTML coverage report
pytest --cov=musicalgestures --cov-report=html

# View detailed coverage
pytest --cov=musicalgestures --cov-report=term-missing
```

### Performance Testing

```bash
# Run tests with timing information
pytest --durations=10

# Profile slow tests
pytest --profile
```

## Test Structure

### Current Test Files

```
tests/
├── test_audio.py          # Audio processing tests
├── test_average.py        # Average image tests  
├── test_centroid.py       # Centroid tracking tests
├── test_init.py           # Package initialization tests
├── test_motionvideo.py    # Motion analysis tests
├── test_ssm.py            # Self-similarity matrix tests
├── test_utils.py          # Utility function tests
└── test_videograms.py     # Videogram generation tests
```

### Test Organization

Tests are organized by functionality and follow this structure:

```python
import pytest
import musicalgestures as mg
from pathlib import Path


@pytest.fixture
def sample_video():
    """Fixture providing sample video path."""
    return mg.examples.dance


@pytest.fixture  
def sample_audio():
    """Fixture providing sample audio path."""
    return mg.examples.pianist


class TestClassName:
    """Test suite for specific functionality."""
    
    def test_basic_functionality(self, sample_video):
        """Test description."""
        # Test implementation
        pass
    
    def test_error_conditions(self):
        """Test error handling.""" 
        # Test implementation
        pass
```

## Writing Tests

### Test Categories

#### 1. Unit Tests

Test individual functions and methods in isolation:

```python
def test_utility_function():
    """Test a utility function."""
    from musicalgestures._utils import generate_outfilename
    
    # Test basic functionality
    result = generate_outfilename('input.mp4', 'output')
    assert result.endswith('_output.mp4')
    
    # Test with custom extension
    result = generate_outfilename('input.avi', 'test', '.png')
    assert result.endswith('_test.png')
```

#### 2. Integration Tests

Test interaction between components:

```python
def test_video_audio_integration(sample_video):
    """Test video and audio integration."""
    mv = mg.MgVideo(sample_video)
    
    # Test that audio component is accessible
    assert mv.audio is not None
    assert hasattr(mv.audio, 'waveform')
    
    # Test audio analysis works
    waveform = mv.audio.waveform()
    assert Path(waveform).exists()
```

#### 3. End-to-End Tests

Test complete workflows:

```python
def test_complete_motion_analysis_workflow(sample_video, tmp_path):
    """Test complete motion analysis from start to finish."""
    # Load video with custom output directory
    mv = mg.MgVideo(sample_video, outdir=str(tmp_path))
    
    # Perform motion analysis
    motion_result = mv.motion()
    
    # Verify outputs exist
    assert Path(motion_result['motion_video']).exists()
    assert Path(motion_result['motion_data']).exists()
    
    # Verify data content
    import pandas as pd
    df = pd.read_csv(motion_result['motion_data'])
    assert len(df) > 0
    assert 'Quantity of Motion' in df.columns
```

### Test Fixtures

Use fixtures for common test data and setup:

```python
@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def test_video_short(tmp_path):
    """Create a short test video for faster tests."""
    # Create minimal test video using OpenCV
    import cv2
    import numpy as np
    
    video_path = tmp_path / "test_short.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(str(video_path), fourcc, 25.0, (640, 480))
    
    # Create 25 frames (1 second at 25fps)
    for i in range(25):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        writer.write(frame)
    
    writer.release()
    return str(video_path)


@pytest.fixture
def mock_video_properties():
    """Mock video properties for testing."""
    return {
        'width': 640,
        'height': 480,
        'fps': 25.0,
        'framecount': 100,
        'length': 4.0
    }
```

### Parameterized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("filtertype,expected", [
    ('Regular', True),
    ('Binary', True), 
    ('Blob', True),
    ('Invalid', False)
])
def test_motion_filtertype(sample_video, filtertype, expected):
    """Test different motion filter types."""
    mv = mg.MgVideo(sample_video)
    
    if expected:
        # Should succeed
        result = mv.motion(filtertype=filtertype)
        assert Path(result['motion_video']).exists()
    else:
        # Should raise error
        with pytest.raises(ValueError):
            mv.motion(filtertype=filtertype)


@pytest.mark.parametrize("starttime,endtime", [
    (0, 5),      # First 5 seconds
    (2, 8),      # Middle section
    (5, 0),      # From 5s to end
])
def test_video_trimming(sample_video, starttime, endtime):
    """Test video trimming with different time ranges."""
    mv = mg.MgVideo(sample_video, starttime=starttime, endtime=endtime)
    
    if endtime > 0:
        expected_length = endtime - starttime
        assert abs(mv.length - expected_length) < 0.5  # Allow small tolerance
    else:
        # endtime=0 means use full video from starttime
        assert mv.length > 0
```

### Mocking External Dependencies

Mock external tools and heavy operations:

```python
from unittest.mock import patch, MagicMock
import pytest


@patch('musicalgestures._utils.ffmpeg_cmd')
def test_video_conversion_mock(mock_ffmpeg, sample_video):
    """Test video conversion without actually running FFmpeg."""
    mock_ffmpeg.return_value = True
    
    from musicalgestures._utils import convert_to_mp4
    result = convert_to_mp4(sample_video)
    
    # Verify FFmpeg was called
    mock_ffmpeg.assert_called_once()
    assert result.endswith('.mp4')


@patch('cv2.VideoCapture')
def test_video_loading_mock(mock_videocap):
    """Test video loading with mocked OpenCV."""
    # Setup mock
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_WIDTH: 640,
        cv2.CAP_PROP_FRAME_HEIGHT: 480,
        cv2.CAP_PROP_FPS: 25.0,
        cv2.CAP_PROP_FRAME_COUNT: 100
    }.get(prop, 0)
    
    mock_videocap.return_value = mock_cap
    
    # Test
    mv = mg.MgVideo('fake_video.mp4')
    assert mv.width == 640
    assert mv.height == 480
    assert mv.fps == 25.0
```

### Error Testing

Test error conditions and edge cases:

```python
def test_file_not_found():
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        mg.MgVideo('nonexistent_file.mp4')


def test_invalid_parameters(sample_video):
    """Test parameter validation."""
    # Invalid threshold
    with pytest.raises(ValueError):
        mv = mg.MgVideo(sample_video)
        mv.motion(thresh=-0.5)  # Negative threshold
    
    # Invalid time range
    with pytest.raises(ValueError):
        mg.MgVideo(sample_video, starttime=10, endtime=5)  # End before start


def test_corrupted_video_handling(tmp_path):
    """Test handling of corrupted video files."""
    # Create fake corrupted video file
    corrupted_video = tmp_path / "corrupted.mp4"
    corrupted_video.write_text("This is not a video file")
    
    with pytest.raises((ValueError, RuntimeError)):
        mg.MgVideo(str(corrupted_video))
```

### Performance Tests

Test performance with larger datasets:

```python
@pytest.mark.slow
def test_large_video_performance(tmp_path):
    """Test performance with larger video (marked as slow)."""
    # This test is marked as 'slow' and can be skipped
    # Run with: pytest -m "not slow" to skip slow tests
    pass


@pytest.mark.parametrize("video_size", [
    (320, 240),   # Small
    (640, 480),   # Medium  
    (1920, 1080), # Large
])
def test_video_size_handling(video_size, tmp_path):
    """Test handling of different video sizes."""
    width, height = video_size
    # Create test video of specified size
    # Test processing
    pass
```

## Test Configuration

### pytest.ini

Create a `pytest.ini` file in the project root:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    requires_ffmpeg: marks tests that require FFmpeg
    requires_opencv: marks tests that require OpenCV
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
```

### Continuous Integration

Example GitHub Actions workflow (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.7, 3.8, 3.9]
        
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov
        
    - name: Install FFmpeg
      run: |
        # OS-specific FFmpeg installation
        
    - name: Run tests
      run: |
        pytest --cov=musicalgestures --cov-report=xml
        
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Test Data Management

### Using Example Videos

Always use the built-in examples for consistency:

```python
def test_with_dance_video():
    """Test using the dance example video."""
    mv = mg.MgVideo(mg.examples.dance)
    # Test implementation


def test_with_pianist_video():  
    """Test using the pianist example video."""
    mv = mg.MgVideo(mg.examples.pianist)
    # Test implementation
```

### Creating Test Data

For specific test scenarios, create minimal test data:

```python
@pytest.fixture
def minimal_video(tmp_path):
    """Create minimal video for testing."""
    import cv2
    import numpy as np
    
    video_path = tmp_path / "minimal.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(str(video_path), fourcc, 10.0, (100, 100))
    
    # Create 10 frames
    for i in range(10):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[i*10:(i+1)*10, :] = 255  # Moving white bar
        writer.write(frame)
    
    writer.release()
    return str(video_path)
```

## Running Specific Test Suites

### By Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests  
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests requiring specific dependencies
pytest -m requires_ffmpeg
```

### By Component

```bash
# Test video functionality
pytest tests/test_video.py tests/test_motionvideo.py

# Test audio functionality
pytest tests/test_audio.py

# Test utilities
pytest tests/test_utils.py
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show full traceback
pytest --tb=long

# Run single test with debugging
pytest -s -vv tests/test_video.py::test_specific_function
```

## Test Best Practices

### General Guidelines

1. **Test one thing at a time** - Each test should focus on a single behavior
2. **Use descriptive names** - Test names should explain what is being tested
3. **Keep tests independent** - Tests should not depend on each other
4. **Use fixtures for setup** - Avoid duplication in test setup
5. **Test both success and failure cases** - Include error condition testing

### Performance Considerations

- Use small test videos when possible
- Mock heavy operations when testing logic
- Mark slow tests appropriately
- Clean up temporary files

### Coverage Goals

- Aim for **>90% code coverage**
- Focus on **critical paths** first
- Test **error conditions** thoroughly
- Include **integration tests** for workflows

## Troubleshooting Tests

### Common Issues

#### FFmpeg Not Found
```bash
# Install FFmpeg for testing
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

#### OpenCV Issues
```bash
# Install OpenCV dependencies
sudo apt install libgl1-mesa-glx  # Ubuntu
```

#### Permission Errors
```bash
# Run tests with proper permissions
sudo pytest  # If needed (not recommended)

# Or fix file permissions
chmod +x test_files/*
```

### Test Environment

Ensure consistent test environment:

```bash
# Clean Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Reset git state (if needed)
git clean -fd

# Fresh virtual environment
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -e .
```

Ready to contribute? Start by running the test suite and then adding tests for your new features!
