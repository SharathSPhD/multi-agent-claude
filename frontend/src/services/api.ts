// API service for backend communication
import { Agent, Task, CreateAgentData, CreateTaskData } from '../types/api';

// Re-export types for backwards compatibility
export type { Agent, Task, CreateAgentData, CreateTaskData } from '../types/api';

const API_BASE = 'http://localhost:8000';

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

  async deleteAgent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/agents/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete agent');
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
    if (!response.ok) throw new Error('Failed to create task');
    return response.json();
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