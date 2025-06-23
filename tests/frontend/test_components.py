"""
Frontend component tests using Jest and React Testing Library
This file contains test specifications for React components
"""

# Note: These are Jest/JavaScript test specifications written in Python format
# They should be converted to actual Jest tests when setting up frontend testing

DASHBOARD_TESTS = """
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ChakraProvider } from '@chakra-ui/react';
import { configureStore } from '@reduxjs/toolkit';
import Dashboard from '../../src/components/Dashboard/Dashboard';
import agentsReducer from '../../src/store/slices/agentsSlice';

// Mock store for testing
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      agents: agentsReducer,
    },
    preloadedState: {
      agents: {
        agents: [],
        loading: false,
        error: null,
        ...initialState.agents
      }
    }
  });
};

const renderWithProviders = (component, { initialState = {} } = {}) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      <ChakraProvider>
        {component}
      </ChakraProvider>
    </Provider>
  );
};

describe('Dashboard Component', () => {
  test('renders dashboard title', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/MCP Multi-Agent System/i)).toBeInTheDocument();
  });

  test('displays agent count', async () => {
    const mockAgents = [
      { id: 1, name: 'Test Agent 1', role: 'tester' },
      { id: 2, name: 'Test Agent 2', role: 'validator' }
    ];
    
    renderWithProviders(<Dashboard />, {
      initialState: {
        agents: { agents: mockAgents }
      }
    });
    
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  test('shows agent observation windows when executions are running', async () => {
    const mockExecution = {
      id: 1,
      agent_id: 1,
      status: 'running',
      agent_response: { analysis: 'Processing...' },
      needs_interaction: false
    };
    
    // Mock API call
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [mockExecution]
    });
    
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Agent Observation/i)).toBeInTheDocument();
    });
  });

  test('displays interaction required badge', async () => {
    const mockExecution = {
      id: 1,
      agent_id: 1,
      status: 'waiting_for_input',
      needs_interaction: true
    };
    
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [mockExecution]
    });
    
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Needs Input/i)).toBeInTheDocument();
    });
  });
});
"""

AGENT_MANAGER_TESTS = """
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ChakraProvider } from '@chakra-ui/react';
import AgentManager from '../../src/components/Agents/AgentManager';

describe('AgentManager Component', () => {
  test('renders agent creation form', () => {
    renderWithProviders(<AgentManager />);
    expect(screen.getByLabelText(/Agent Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Role/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/System Prompt/i)).toBeInTheDocument();
  });

  test('creates new agent on form submission', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: 'Test Agent', role: 'tester' })
    });

    renderWithProviders(<AgentManager />);
    
    fireEvent.change(screen.getByLabelText(/Agent Name/i), {
      target: { value: 'Test Agent' }
    });
    fireEvent.change(screen.getByLabelText(/Role/i), {
      target: { value: 'tester' }
    });
    
    fireEvent.click(screen.getByText(/Create Agent/i));
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/agents', expect.any(Object));
    });
  });

  test('displays validation errors', async () => {
    renderWithProviders(<AgentManager />);
    
    // Try to submit without required fields
    fireEvent.click(screen.getByText(/Create Agent/i));
    
    await waitFor(() => {
      expect(screen.getByText(/Agent name is required/i)).toBeInTheDocument();
    });
  });

  test('shows agent list', async () => {
    const mockAgents = [
      { id: 1, name: 'Agent 1', role: 'tester' },
      { id: 2, name: 'Agent 2', role: 'validator' }
    ];
    
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAgents
    });
    
    renderWithProviders(<AgentManager />);
    
    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument();
      expect(screen.getByText('Agent 2')).toBeInTheDocument();
    });
  });
});
"""

TASK_MANAGER_TESTS = """
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TaskManager from '../../src/components/Tasks/TaskManager';

describe('TaskManager Component', () => {
  test('renders task creation form', () => {
    renderWithProviders(<TaskManager />);
    expect(screen.getByLabelText(/Task Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Priority/i)).toBeInTheDocument();
  });

  test('creates new task on form submission', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: 'Test Task', description: 'Test description' })
    });

    renderWithProviders(<TaskManager />);
    
    fireEvent.change(screen.getByLabelText(/Task Name/i), {
      target: { value: 'Test Task' }
    });
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Test description' }
    });
    
    fireEvent.click(screen.getByText(/Create Task/i));
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/tasks', expect.any(Object));
    });
  });

  test('displays task list with execution buttons', async () => {
    const mockTasks = [
      { id: 1, name: 'Task 1', description: 'Description 1', priority: 1 },
      { id: 2, name: 'Task 2', description: 'Description 2', priority: 2 }
    ];
    
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockTasks
    });
    
    renderWithProviders(<TaskManager />);
    
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
      expect(screen.getAllByText(/Execute/i)).toHaveLength(2);
    });
  });
});
"""

ORCHESTRATOR_TESTS = """
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AdvancedOrchestrator from '../../src/components/Orchestration/AdvancedOrchestrator';

describe('AdvancedOrchestrator Component', () => {
  test('renders workflow pattern selection', () => {
    renderWithProviders(<AdvancedOrchestrator />);
    expect(screen.getByText(/Workflow Patterns/i)).toBeInTheDocument();
  });

  test('displays AI analysis recommendation', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        recommended_pattern: 'Orchestrator',
        analysis: 'Best for coordinated execution'
      })
    });

    renderWithProviders(<AdvancedOrchestrator />);
    
    fireEvent.click(screen.getByText(/Analyze Workflow/i));
    
    await waitFor(() => {
      expect(screen.getByText(/Best for coordinated execution/i)).toBeInTheDocument();
    });
  });

  test('starts workflow execution', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ execution_id: 'exec_123', status: 'started' })
    });

    renderWithProviders(<AdvancedOrchestrator />);
    
    fireEvent.click(screen.getByText(/Start Execution/i));
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/orchestration/execute', expect.any(Object));
    });
  });

  test('shows real-time execution monitoring', async () => {
    // Mock WebSocket
    const mockWebSocket = {
      addEventListener: jest.fn(),
      send: jest.fn(),
      close: jest.fn()
    };
    global.WebSocket = jest.fn(() => mockWebSocket);

    renderWithProviders(<AdvancedOrchestrator />);
    
    expect(global.WebSocket).toHaveBeenCalledWith(expect.stringContaining('ws://'));
  });
});
"""

# Frontend test configuration
FRONTEND_TEST_CONFIG = {
    "jest_config": {
        "testEnvironment": "jsdom",
        "setupFilesAfterEnv": ["<rootDir>/src/setupTests.js"],
        "moduleNameMapping": {
            "\\.(css|less|scss)$": "identity-obj-proxy"
        },
        "transform": {
            "^.+\\.(js|jsx|ts|tsx)$": "babel-jest"
        }
    },
    "test_scripts": {
        "test": "jest",
        "test_watch": "jest --watch",
        "test_coverage": "jest --coverage"
    }
}


def create_frontend_test_files():
    """
    Instructions for creating frontend test files:
    
    1. Install testing dependencies:
       npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
    
    2. Create setupTests.js in src/:
       import '@testing-library/jest-dom';
    
    3. Create test files in src/__tests__/ or alongside components:
       - Dashboard.test.tsx
       - AgentManager.test.tsx  
       - TaskManager.test.tsx
       - AdvancedOrchestrator.test.tsx
    
    4. Update package.json with test scripts
    
    5. Configure Jest in package.json or jest.config.js
    """
    return {
        "dashboard_test": DASHBOARD_TESTS,
        "agent_manager_test": AGENT_MANAGER_TESTS,
        "task_manager_test": TASK_MANAGER_TESTS,
        "orchestrator_test": ORCHESTRATOR_TESTS,
        "config": FRONTEND_TEST_CONFIG
    }