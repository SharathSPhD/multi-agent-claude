// Advanced orchestration API service
// Dynamic API base to work with both localhost and WSL IP
const API_BASE = (() => {
  if (typeof window !== 'undefined') {
    // Use the same hostname as the frontend, but port 8000
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return 'http://localhost:8000'; // Fallback for SSR
})();

export interface WorkflowAnalysis {
  recommended_workflow: string;
  analysis: {
    agent_count: number;
    task_count: number;
    has_dependencies: boolean;
    user_objective: string;
  };
}

export interface WorkflowPattern {
  id: string;
  name: string;
  description: string;
  workflow_type: string;
  agent_ids: string[];
  task_ids: string[];
  user_objective: string;
  project_directory?: string;
  status: string;
  created_at: string;
  updated_at: string;
  metadata: {
    agent_count: number;
    task_count: number;
    existing_agents: number;
    existing_tasks: number;
    integrity_check: {
      agents_valid: boolean;
      tasks_valid: boolean;
    };
  };
}

export interface WorkflowExecution {
  id: string;
  pattern_id: string;
  status: string;
  started_at: string;
  updated_at: string;
  current_step: number;
  total_steps: number;
  progress_percentage: number;
  active_agents: string[];
  completed_tasks: string[];
  failed_tasks: string[];
  agent_communications: AgentComm[];
  step_outputs: Record<string, any>;
  iteration_count: number;
}

export interface AgentComm {
  id: string;
  execution_id: string;
  from_agent_id: string;
  to_agent_id: string;
  message: string;
  message_type: string;
  timestamp: string;
  context: Record<string, any>;
}

export interface WorkflowTypeInfo {
  name: string;
  description: string;
  use_cases: string[];
  advantages: string[];
  ideal_for: string;
}

export interface WorkflowTypes {
  [key: string]: WorkflowTypeInfo;
}

class AdvancedOrchestrationService {
  
  async analyzeWorkflow(agentIds: string[], taskIds: string[], objective: string = ''): Promise<WorkflowAnalysis> {
    const response = await fetch(`${API_BASE}/api/workflows/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agents_ids: agentIds,
        task_ids: taskIds,
        user_objective: objective,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to analyze workflow');
    return response.json();
  }

  async createWorkflowPattern(data: {
    name: string;
    description: string;
    agent_ids: string[];
    task_ids: string[];
    user_objective?: string;
    workflow_type?: string;
    project_directory?: string;
  }): Promise<WorkflowPattern> {
    const response = await fetch(`${API_BASE}/api/workflows/patterns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to create workflow pattern');
    return response.json();
  }

  async getWorkflowPatterns(): Promise<WorkflowPattern[]> {
    const response = await fetch(`${API_BASE}/api/workflows/patterns`);
    if (!response.ok) throw new Error('Failed to fetch workflow patterns');
    const data = await response.json();
    
    // Handle both old format (direct array) and new format (wrapped in data.patterns)
    if (Array.isArray(data)) {
      return data; // Old format
    } else if (data.success && data.data && Array.isArray(data.data.patterns)) {
      return data.data.patterns; // New enhanced format
    } else {
      console.warn('Unexpected workflow patterns response format:', data);
      return []; // Fallback to empty array
    }
  }

  async executeWorkflow(patternId: string, context: Record<string, any> = {}): Promise<WorkflowExecution> {
    const response = await fetch(`${API_BASE}/api/workflows/execute/${patternId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(context),
    });
    
    if (!response.ok) throw new Error('Failed to execute workflow');
    const data = await response.json();
    
    // Handle enhanced backend response format
    if (data.success && data.data) {
      // Transform the nested response to match WorkflowExecution interface
      return {
        id: data.data.execution_id,
        pattern_id: data.data.pattern_id,
        status: data.data.status,
        started_at: data.data.started_at,
        updated_at: data.data.completed_at || data.data.started_at,
        current_step: 0,
        total_steps: 0,
        progress_percentage: data.data.progress_percentage || 0,
        active_agents: [],
        completed_tasks: [],
        failed_tasks: [],
        agent_communications: [],
        step_outputs: data.data.results || {},
        iteration_count: 0
      };
    }
    
    // Fallback for old format
    return data;
  }

  async getExecutionStatus(executionId: string): Promise<WorkflowExecution> {
    const response = await fetch(`${API_BASE}/api/workflows/executions/${executionId}`);
    if (!response.ok) throw new Error('Failed to get execution status');
    return response.json();
  }

  async getActiveExecutions(): Promise<WorkflowExecution[]> {
    const response = await fetch(`${API_BASE}/api/workflows/executions`);
    if (!response.ok) throw new Error('Failed to get active executions');
    const data = await response.json();
    
    // Handle the enhanced response format from backend
    if (data.success && data.data && data.data.executions) {
      return data.data.executions.map((execution: any) => ({
        id: execution.id,
        pattern_id: execution.pattern_id,
        status: execution.status,
        started_at: execution.started_at,
        updated_at: execution.completed_at || execution.started_at,
        current_step: 0,
        total_steps: 0,
        progress_percentage: execution.progress_percentage || 0,
        active_agents: [],
        completed_tasks: [],
        failed_tasks: [],
        agent_communications: [],
        step_outputs: execution.results || {},
        iteration_count: 0
      }));
    }
    
    // Fallback for direct array format
    return Array.isArray(data) ? data : [];
  }

  async getAgentCommunications(executionId: string): Promise<AgentComm[]> {
    const response = await fetch(`${API_BASE}/api/workflows/communications/${executionId}`);
    if (!response.ok) throw new Error('Failed to get agent communications');
    return response.json();
  }

  async getWorkflowTypes(): Promise<WorkflowTypes> {
    const response = await fetch(`${API_BASE}/api/workflows/types`);
    if (!response.ok) throw new Error('Failed to get workflow types');
    const data = await response.json();
    
    // Handle enhanced response format
    if (data.success && data.data && data.data.workflow_types) {
      return data.data.workflow_types;
    }
    return data;
  }

  async updateWorkflowPattern(patternId: string, data: {
    name: string;
    description: string;
    agent_ids: string[];
    task_ids: string[];
    user_objective?: string;
    workflow_type?: string;
    project_directory?: string;
  }): Promise<WorkflowPattern> {
    const response = await fetch(`${API_BASE}/api/workflows/patterns/${patternId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to update workflow pattern');
    return response.json();
  }

  async deleteWorkflowPattern(patternId: string, force: boolean = false): Promise<void> {
    const url = force 
      ? `${API_BASE}/api/workflows/patterns/${patternId}?force=true`
      : `${API_BASE}/api/workflows/patterns/${patternId}`;
      
    const response = await fetch(url, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`${response.status}: ${errorData.error?.message || 'Failed to delete workflow pattern'}`);
    }
  }

  async abortWorkflowExecution(executionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/workflows/executions/${executionId}/abort`, {
      method: 'POST',
    });
    
    if (!response.ok) throw new Error('Failed to abort workflow execution');
  }

  async deleteWorkflowExecution(executionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/workflows/executions/${executionId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) throw new Error('Failed to delete workflow execution');
  }
}

export const advancedOrchestrationService = new AdvancedOrchestrationService();