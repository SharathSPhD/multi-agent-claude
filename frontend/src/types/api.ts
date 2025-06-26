// API Types aligned with backend schemas

export type AgentStatus = 'idle' | 'executing' | 'error' | 'stopped';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  system_prompt: string;
  capabilities: string[];
  tools: string[];
  objectives: string[];
  constraints: string[];
  status: AgentStatus;
  memory_settings?: Record<string, any>;
  execution_settings?: Record<string, any>;
  last_active?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  expected_output?: string;
  assigned_agent_ids?: string[];
  agent_id?: string; // For backwards compatibility
  assigned_agents?: Agent[];
  resources: string[];
  dependencies: string[];
  priority: TaskPriority;
  deadline?: string;
  estimated_duration?: number;
  status: TaskStatus;
  results?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentData {
  name: string;
  role: string;
  description: string;
  system_prompt: string;
  capabilities?: string[];
  tools?: string[];
  objectives?: string[];
  constraints?: string[];
  memory_settings?: Record<string, any>;
  execution_settings?: Record<string, any>;
}

export interface CreateTaskData {
  title: string;
  description: string;
  expected_output?: string;
  assigned_agent_ids?: string[];
  agent_id?: string; // For backwards compatibility
  resources?: string[];
  dependencies?: string[];
  priority?: TaskPriority;
  deadline?: string;
  estimated_duration?: number;
}

export interface AgentUpdate {
  name?: string;
  role?: string;
  description?: string;
  system_prompt?: string;
  capabilities?: string[];
  tools?: string[];
  objectives?: string[];
  constraints?: string[];
  memory_settings?: Record<string, any>;
  execution_settings?: Record<string, any>;
  status?: AgentStatus;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  expected_output?: string;
  assigned_agent_ids?: string[];
  resources?: string[];
  dependencies?: string[];
  priority?: TaskPriority;
  deadline?: string;
  estimated_duration?: number;
  status?: TaskStatus;
}

export interface Execution {
  id: string;
  task_id: string;
  agent_id: string;
  status: TaskStatus;
  started_at: string;
  completed_at?: string;
  results?: Record<string, any>;
  error_message?: string;
}