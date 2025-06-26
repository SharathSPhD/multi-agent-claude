// API service for backend communication
import { Agent, Task, CreateAgentData, CreateTaskData, AgentUpdate, TaskUpdate, AgentStatus } from '../types/api';

// Re-export types for backwards compatibility
export type { Agent, Task, CreateAgentData, CreateTaskData, AgentUpdate, TaskUpdate, AgentStatus } from '../types/api';

// Dynamic API base to work with both localhost and WSL IP
const API_BASE = (() => {
  if (typeof window !== 'undefined') {
    // Use the same hostname as the frontend, but port 8000
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return 'http://localhost:8000'; // Fallback for SSR
})();

class ApiService {
  // Agent operations
  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${API_BASE}/api/agents`);
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  }

  async createAgent(data: CreateAgentData): Promise<Agent> {
    const response = await fetch(`${API_BASE}/api/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create agent');
    return response.json();
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await fetch(`${API_BASE}/api/agents/${id}`);
    if (!response.ok) throw new Error('Failed to fetch agent');
    return response.json();
  }

  async updateAgent(id: string, data: AgentUpdate): Promise<Agent> {
    const response = await fetch(`${API_BASE}/api/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update agent');
    return response.json();
  }

  async deleteAgent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/agents/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete agent');
  }

  async setAgentStatus(id: string, status: AgentStatus): Promise<Agent> {
    return this.updateAgent(id, { status });
  }

  // Task operations
  async getTasks(): Promise<Task[]> {
    const response = await fetch(`${API_BASE}/api/tasks`);
    if (!response.ok) throw new Error('Failed to fetch tasks');
    return response.json();
  }

  async createTask(data: CreateTaskData): Promise<Task> {
    const response = await fetch(`${API_BASE}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.text();
      console.error('Create task error response:', errorData);
      throw new Error(`Failed to create task: ${response.status} - ${errorData}`);
    }
    return response.json();
  }

  async updateTask(id: string, data: TaskUpdate): Promise<Task> {
    const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update task');
    return response.json();
  }

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete task');
  }

  async executeTask(taskId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/tasks/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId }),
    });
    if (!response.ok) throw new Error('Failed to execute task');
  }
}

export const apiService = new ApiService();