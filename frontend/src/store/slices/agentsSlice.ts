import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Agent, CreateAgentData, AgentStatus, AgentUpdate } from '../../types/api';
import { apiService } from '../../services/api';

interface AgentsState {
  agents: Agent[];
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status?: AgentStatus;
    role?: string;
    search?: string;
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

const initialState: AgentsState = {
  agents: [],
  selectedAgent: null,
  isLoading: false,
  error: null,
  filters: {},
  pagination: {
    page: 1,
    limit: 20,
    total: 0
  }
};

// Async thunks
export const fetchAgents = createAsyncThunk(
  'agents/fetchAgents',
  async () => {
    const response = await apiService.getAgents();
    return response;
  }
);

export const fetchAgent = createAsyncThunk(
  'agents/fetchAgent',
  async (agentId: string) => {
    const response = await apiService.getAgent(agentId);
    return response;
  }
);

export const createAgent = createAsyncThunk(
  'agents/createAgent',
  async (agentData: CreateAgentData) => {
    const response = await apiService.createAgent(agentData);
    return response;
  }
);

export const updateAgent = createAsyncThunk(
  'agents/updateAgent',
  async ({ id, updates }: { id: string; updates: AgentUpdate }) => {
    const response = await apiService.updateAgent(id, updates);
    return response;
  }
);

export const deleteAgent = createAsyncThunk(
  'agents/deleteAgent',
  async (agentId: string) => {
    await apiService.deleteAgent(agentId);
    return agentId;
  }
);

export const startAgent = createAsyncThunk(
  'agents/startAgent',
  async (agentId: string) => {
    // Update agent status to executing
    const response = await apiService.updateAgent(agentId, { status: 'executing' });
    return response;
  }
);

export const stopAgent = createAsyncThunk(
  'agents/stopAgent',
  async (agentId: string) => {
    // Update agent status to idle
    const response = await apiService.updateAgent(agentId, { status: 'idle' });
    return response;
  }
);

const agentsSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    setSelectedAgent: (state, action: PayloadAction<Agent | null>) => {
      state.selectedAgent = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<AgentsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setPagination: (state, action: PayloadAction<Partial<AgentsState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    updateAgentStatus: (state, action: PayloadAction<{ agentId: string; status: AgentStatus }>) => {
      const agent = state.agents.find(a => a.id === action.payload.agentId);
      if (agent) {
        agent.status = action.payload.status;
        agent.last_active = new Date().toISOString();
      }
      if (state.selectedAgent && state.selectedAgent.id === action.payload.agentId) {
        state.selectedAgent.status = action.payload.status;
        state.selectedAgent.last_active = new Date().toISOString();
      }
    },
    addAgentLog: (state, action: PayloadAction<{ agentId: string; log: any }>) => {
      // This could be used for real-time log updates
      const agent = state.agents.find(a => a.id === action.payload.agentId);
      if (agent) {
        // Add log to agent's execution settings or a logs array if we add one
      }
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch agents
      .addCase(fetchAgents.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchAgents.fulfilled, (state, action) => {
        state.isLoading = false;
        state.agents = action.payload;
        state.pagination.total = action.payload.length;
      })
      .addCase(fetchAgents.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch agents';
      })
      
      // Fetch single agent
      .addCase(fetchAgent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchAgent.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selectedAgent = action.payload;
        
        // Update agent in the list if it exists
        const index = state.agents.findIndex(a => a.id === action.payload.id);
        if (index !== -1) {
          state.agents[index] = action.payload;
        }
      })
      .addCase(fetchAgent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch agent';
      })
      
      // Create agent
      .addCase(createAgent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createAgent.fulfilled, (state, action) => {
        state.isLoading = false;
        state.agents.unshift(action.payload);
        state.pagination.total += 1;
      })
      .addCase(createAgent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create agent';
      })
      
      // Update agent
      .addCase(updateAgent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateAgent.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.agents.findIndex(a => a.id === action.payload.id);
        if (index !== -1) {
          state.agents[index] = action.payload;
        }
        if (state.selectedAgent && state.selectedAgent.id === action.payload.id) {
          state.selectedAgent = action.payload;
        }
      })
      .addCase(updateAgent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to update agent';
      })
      
      // Delete agent
      .addCase(deleteAgent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteAgent.fulfilled, (state, action) => {
        state.isLoading = false;
        state.agents = state.agents.filter(a => a.id !== action.payload);
        state.pagination.total -= 1;
        if (state.selectedAgent && state.selectedAgent.id === action.payload) {
          state.selectedAgent = null;
        }
      })
      .addCase(deleteAgent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to delete agent';
      })
      
      // Start agent
      .addCase(startAgent.fulfilled, (state, action) => {
        const index = state.agents.findIndex(a => a.id === action.payload.id);
        if (index !== -1) {
          state.agents[index] = action.payload;
        }
        if (state.selectedAgent && state.selectedAgent.id === action.payload.id) {
          state.selectedAgent = action.payload;
        }
      })
      
      // Stop agent
      .addCase(stopAgent.fulfilled, (state, action) => {
        const index = state.agents.findIndex(a => a.id === action.payload.id);
        if (index !== -1) {
          state.agents[index] = action.payload;
        }
        if (state.selectedAgent && state.selectedAgent.id === action.payload.id) {
          state.selectedAgent = action.payload;
        }
      });
  }
});

export const {
  setSelectedAgent,
  setFilters,
  clearFilters,
  setPagination,
  updateAgentStatus,
  addAgentLog,
  clearError
} = agentsSlice.actions;

// Selectors
export const selectAgents = (state: { agents: AgentsState }) => state.agents.agents;
export const selectSelectedAgent = (state: { agents: AgentsState }) => state.agents.selectedAgent;
export const selectAgentsLoading = (state: { agents: AgentsState }) => state.agents.isLoading;
export const selectAgentsError = (state: { agents: AgentsState }) => state.agents.error;
export const selectAgentsFilters = (state: { agents: AgentsState }) => state.agents.filters;

// Filtered agents selector
export const selectFilteredAgents = (state: { agents: AgentsState }) => {
  const { agents, filters } = state.agents;
  
  return agents.filter(agent => {
    if (filters.status && agent.status !== filters.status) return false;
    if (filters.role && agent.role !== filters.role) return false;
    if (filters.search) {
      const search = filters.search.toLowerCase();
      return (
        agent.name.toLowerCase().includes(search) ||
        agent.description?.toLowerCase().includes(search) ||
        agent.capabilities.some(cap => cap.toLowerCase().includes(search))
      );
    }
    return true;
  });
};

// Active agents selector
export const selectActiveAgents = (state: { agents: AgentsState }) => {
  return state.agents.agents.filter(agent => agent.status === 'executing');
};

// Agent by ID selector
export const selectAgentById = (state: { agents: AgentsState }, agentId: string) => {
  return state.agents.agents.find(agent => agent.id === agentId);
};

export default agentsSlice.reducer;