"""Tests for PatreonCollectionPolicy."""
import sys
from pathlib import Path

# Add examples/patreon to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from policy_patreon import PatreonCollectionPolicy
from task_spec_patreon import PatreonCollectionTaskSpec
from browser_agent.agent.task_spec import TaskState
from browser_agent.browser.observation import PageObservation
from browser_agent.browser.actions import Navigate, WaitForUser, WaitForSelector, ExtractLinks


def test_patreon_policy_initial_navigate():
    """Test that policy navigates to Patreon initially."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    state = TaskState()
    obs = PageObservation(url="https://example.com", title="Other", buttons=[], inputs=[])
    
    action = policy.decide(obs, task, state)
    
    assert isinstance(action, Navigate)
    assert action.url == "https://www.patreon.com/"


def test_patreon_policy_wait_for_auth():
    """Test that policy waits for user authentication."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    state = TaskState()
    obs = PageObservation(url="https://www.patreon.com/", title="Patreon", buttons=[], inputs=[])
    
    action = policy.decide(obs, task, state)
    
    assert isinstance(action, WaitForUser)
    assert "log in" in action.message.lower()
    assert task.authenticated is True  # Should be set by the policy


def test_patreon_policy_navigate_to_collection():
    """Test that policy navigates to collection after auth."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    state = TaskState()
    obs = PageObservation(url="https://www.patreon.com/", title="Patreon", buttons=[], inputs=[])
    
    action = policy.decide(obs, task, state)
    
    assert isinstance(action, Navigate)
    assert action.url == "https://www.patreon.com/collection/1611241?view=expanded"
    assert task.navigated_to_collection is True


def test_patreon_policy_wait_for_selector():
    """Test that policy waits for content to load."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    task.navigated_to_collection = True
    state = TaskState(steps=4)  # First time on collection page
    obs = PageObservation(
        url="https://www.patreon.com/collection/1611241",
        title="Collection",
        buttons=[],
        inputs=[]
    )
    
    action = policy.decide(obs, task, state)

    assert isinstance(action, WaitForSelector)
    assert action.selector == "a[href*='/posts/']"
def test_patreon_policy_extract_links():
    """Test that policy extracts links after waiting."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    task.navigated_to_collection = True
    state = TaskState(steps=5)  # After wait step
    obs = PageObservation(
        url="https://www.patreon.com/collection/1611241",
        title="Collection",
        buttons=[],
        inputs=[]
    )
    
    action = policy.decide(obs, task, state)
    
    assert isinstance(action, ExtractLinks)
    assert "collection=1611241" in action.pattern
    assert task.extracted_links is True


def test_patreon_policy_fallback_navigate():
    """Test fallback behavior when in unexpected state."""
    policy = PatreonCollectionPolicy()
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    task.navigated_to_collection = True
    task.extracted_links = True
    state = TaskState(steps=10)
    obs = PageObservation(url="https://other.com", title="Other", buttons=[], inputs=[])
    
    action = policy.decide(obs, task, state)
    
    assert isinstance(action, Navigate)
    assert action.url == "https://www.patreon.com/"
