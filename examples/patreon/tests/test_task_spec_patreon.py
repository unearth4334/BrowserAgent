"""Tests for PatreonCollectionTaskSpec."""
import sys
from pathlib import Path

# Add examples/patreon to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_spec_patreon import PatreonCollectionTaskSpec
from browser_agent.agent.task_spec import TaskState
from browser_agent.browser.observation import PageObservation


def test_patreon_collection_task_spec_initial_url():
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    assert task.initial_url() == "https://www.patreon.com/"


def test_patreon_collection_task_spec_collection_url():
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    assert task.collection_url() == "https://www.patreon.com/collection/1611241?view=expanded"


def test_patreon_collection_task_spec_is_done():
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    task.navigated_to_collection = True
    task.extracted_links = True
    
    state = TaskState()
    obs = PageObservation(
        url="https://www.patreon.com/collection/1611241",
        title="Collection",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is True


def test_patreon_collection_task_spec_is_not_done_without_auth():
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = False
    task.navigated_to_collection = True
    task.extracted_links = True
    
    state = TaskState()
    obs = PageObservation(
        url="https://www.patreon.com/collection/1611241",
        title="Collection",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is False


def test_patreon_collection_task_spec_is_not_done_without_extraction():
    task = PatreonCollectionTaskSpec(collection_id="1611241")
    task.authenticated = True
    task.navigated_to_collection = True
    task.extracted_links = False
    
    state = TaskState()
    obs = PageObservation(
        url="https://www.patreon.com/collection/1611241",
        title="Collection",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is False
