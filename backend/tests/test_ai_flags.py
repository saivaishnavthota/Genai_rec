"""Tests for AI flag tracking"""
import pytest
from app.ai_interview.utils.flag_tracker import (
    FlagTracker, create_head_turn_tracker, create_face_absent_tracker,
    create_multi_face_tracker, create_phone_tracker
)


def test_head_turn_tracker_moderate():
    """Test head turn tracker emits moderate flag"""
    tracker = create_head_turn_tracker()
    
    # Simulate head turn >35° for 2.5 seconds
    t = 0.0
    flags = []
    
    for i in range(25):  # 2.5 seconds at 10Hz
        t = i * 0.1
        conf = 0.65  # Maps to ~35° yaw
        window = tracker.update(t, conf, {"yaw": 35})
        if window:
            flags.append(window)
    
    assert len(flags) > 0
    assert flags[0].severity.value == "moderate"
    assert flags[0].t_end - flags[0].t_start >= 2.0


def test_head_turn_tracker_high():
    """Test head turn tracker emits high severity flag"""
    tracker = create_head_turn_tracker()
    
    # Simulate head turn ≥45° for 3.5 seconds
    t = 0.0
    flags = []
    
    for i in range(35):  # 3.5 seconds
        t = i * 0.1
        conf = 0.8  # Maps to ~45° yaw
        window = tracker.update(t, conf, {"yaw": 45})
        if window:
            flags.append(window)
    
    assert len(flags) > 0
    assert flags[0].severity.value == "high"
    assert flags[0].t_end - flags[0].t_start >= 3.0


def test_face_absent_tracker():
    """Test face absent tracker"""
    tracker = create_face_absent_tracker()
    
    # Simulate face absent for 5 seconds (should trigger moderate)
    t = 0.0
    flags = []
    
    for i in range(50):  # 5 seconds
        t = i * 0.1
        conf = 0.6  # Face absent = high confidence in absence
        window = tracker.update(t, conf)
        if window:
            flags.append(window)
    
    assert len(flags) > 0
    assert flags[0].severity.value == "moderate"


def test_phone_tracker():
    """Test phone detection tracker"""
    tracker = create_phone_tracker()
    
    # Simulate phone detection with confidence 0.70 for 1.5 seconds
    t = 0.0
    flags = []
    
    for i in range(15):  # 1.5 seconds
        t = i * 0.1
        conf = 0.70
        window = tracker.update(t, conf, {"class": "cell phone"})
        if window:
            flags.append(window)
    
    assert len(flags) > 0
    assert flags[0].severity.value == "moderate"


def test_phone_tracker_high():
    """Test phone tracker emits high severity"""
    tracker = create_phone_tracker()
    
    # Simulate phone detection with confidence 0.80 for 2.5 seconds
    t = 0.0
    flags = []
    
    for i in range(25):  # 2.5 seconds
        t = i * 0.1
        conf = 0.80  # High confidence
        window = tracker.update(t, conf, {"class": "cell phone"})
        if window:
            flags.append(window)
    
    assert len(flags) > 0
    assert flags[0].severity.value == "high"


def test_flag_tracker_cooldown():
    """Test flag tracker respects cooldown period"""
    tracker = create_head_turn_tracker()
    
    # Emit first flag
    t = 0.0
    for i in range(25):
        t = i * 0.1
        window = tracker.update(t, 0.65)
        if window:
            break
    
    # Immediately try to emit another flag (should be blocked by cooldown)
    flag_count = 0
    for i in range(10):
        t = t + i * 0.1
        window = tracker.update(t, 0.65)
        if window:
            flag_count += 1
    
    # Should only have one flag due to cooldown
    assert flag_count <= 1

