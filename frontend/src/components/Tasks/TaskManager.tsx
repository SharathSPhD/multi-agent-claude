import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Button,
  SimpleGrid,
  Card,
  CardBody,
  Text,
  Badge,
  VStack,
  HStack,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  useToast,
  IconButton,
  Flex,
} from '@chakra-ui/react';
import { FiPlus, FiEdit, FiCheckSquare, FiTrash2, FiUpload } from 'react-icons/fi';
import { apiService, Agent, Task, CreateTaskData, TaskUpdate } from '../../services/api';

export default function TaskManager() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isFileMode, setIsFileMode] = useState(false);
  const [formData, setFormData] = useState<CreateTaskData>({
    title: '',
    description: '',
    assigned_agent_ids: [],
    expected_output: '',
    resources: [],
    dependencies: [],
    priority: 'medium',
    deadline: '',
    estimated_duration: 0,
  });
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const fetchData = async () => {
    try {
      const [tasksData, agentsData] = await Promise.all([
        apiService.getTasks(),
        apiService.getAgents(),
      ]);
      setTasks(tasksData);
      setAgents(agentsData);
    } catch (error) {
      toast({
        title: 'Error fetching data',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const getApiBase = () => {
    if (typeof window !== 'undefined') {
      const { protocol, hostname } = window.location;
      return `${protocol}//${hostname}:8000`;
    }
    return 'http://localhost:8000';
  };

  const loadTasksFromFiles = async () => {
    const directory = ''; // Will be set from project directory selection
    setLoadingFiles(true);
    
    try {
      const response = await fetch(`${getApiBase()}/api/project/load-from-directory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directory, force_reload: true })
      });
      
      if (!response.ok) {
        throw new Error('Failed to load tasks from files');
      }
      
      const results = await response.json();
      
      toast({
        title: 'Tasks loaded successfully',
        description: `Loaded ${results.tasks_loaded} tasks from ${results.files_processed.length} files`,
        status: 'success',
        duration: 5000
      });

      if (results.errors.length > 0) {
        toast({
          title: 'Some errors occurred',
          description: `${results.errors.length} errors during loading`,
          status: 'warning',
          duration: 3000
        });
      }

      // Refresh tasks list
      fetchData();
      
    } catch (error) {
      toast({
        title: 'Error loading tasks',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000
      });
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every 5 seconds to see task status updates
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title || !formData.description || (!formData.assigned_agent_ids || formData.assigned_agent_ids.length === 0)) {
      toast({
        title: 'Please fill in all required fields (title, description, and agent)',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      // Clean up the form data - remove empty strings and arrays
      const cleanedData = {
        ...formData,
        expected_output: formData.expected_output || undefined,
        estimated_duration: formData.estimated_duration || undefined,
        deadline: formData.deadline || undefined,
        resources: formData.resources?.length ? formData.resources : undefined,
        dependencies: formData.dependencies?.length ? formData.dependencies : undefined,
      };
      
      console.log('Submitting task data:', JSON.stringify(cleanedData, null, 2));
      
      if (editingTask) {
        // Update existing task
        await apiService.updateTask(editingTask.id, cleanedData as TaskUpdate);
        toast({
          title: 'Task updated successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Create new task
        await apiService.createTask(cleanedData);
        toast({
          title: 'Task created successfully',
          status: 'success',
          duration: 3000,
        });
      }
      
      resetForm();
      onClose();
      fetchData();
    } catch (error) {
      console.error('Task submission error:', error);
      toast({
        title: editingTask ? 'Error updating task' : 'Error creating task',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleExecute = async (taskId: string) => {
    try {
      await apiService.executeTask(taskId);
      toast({
        title: 'Task execution started',
        status: 'success',
        duration: 3000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error executing task',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const deleteTask = async (taskId: string, taskTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete task "${taskTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await apiService.deleteTask(taskId);
      toast({
        title: 'Task deleted successfully',
        status: 'success',
        duration: 3000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error deleting task',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const deleteAllTasks = async () => {
    if (!window.confirm(`Are you sure you want to delete ALL ${tasks.length} tasks? This action cannot be undone.`)) {
      return;
    }

    try {
      // Delete all tasks one by one
      await Promise.all(tasks.map(task => apiService.deleteTask(task.id)));
      toast({
        title: `Successfully deleted ${tasks.length} tasks`,
        status: 'success',
        duration: 3000,
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error deleting tasks',
        description: error instanceof Error ? error.message : 'Some tasks may not have been deleted',
        status: 'error',
        duration: 3000,
      });
      fetchData(); // Refresh to show current state
    }
  };

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Unknown Agent';
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      assigned_agent_ids: [],
      expected_output: '',
      resources: [],
      dependencies: [],
      priority: 'medium',
      deadline: '',
      estimated_duration: 0,
    });
    setEditingTask(null);
    setIsFileMode(false);
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    
    // Extract agent IDs from assigned_agents array or use assigned_agent_ids if available
    const agentIds = task.assigned_agent_ids || 
                    (task.assigned_agents ? task.assigned_agents.map(agent => agent.id) : []);
    
    setFormData({
      title: task.title,
      description: task.description,
      assigned_agent_ids: agentIds,
      expected_output: task.expected_output || '',
      resources: task.resources || [],
      dependencies: task.dependencies || [],
      priority: task.priority || 'medium',
      deadline: task.deadline || '',
      estimated_duration: task.estimated_duration || 0,
    });
    setIsFileMode(false);
    onOpen();
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const taskData = JSON.parse(text);
      
      // Validate JSON structure
      if (!taskData.title || !taskData.description) {
        throw new Error('Invalid task JSON: missing required fields (title, description)');
      }

      setFormData({
        title: taskData.title,
        description: taskData.description,
        assigned_agent_ids: taskData.assigned_agent_ids || [],
        expected_output: taskData.expected_output || '',
        resources: taskData.resources || [],
        dependencies: taskData.dependencies || [],
        priority: taskData.priority || 'medium',
        deadline: taskData.deadline || '',
        estimated_duration: taskData.estimated_duration || 0,
      });
      
      toast({
        title: 'Task loaded from file',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error loading task file',
        description: error instanceof Error ? error.message : 'Invalid JSON file',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'executing': return 'blue';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  if (loading) {
    return <Text>Loading tasks...</Text>;
  }

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading>Task Management</Heading>
        <HStack spacing={3}>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue" 
            onClick={() => {
              resetForm();
              onOpen();
            }}
            isDisabled={agents.length === 0}
          >
            Create Task
          </Button>
        </HStack>
      </Flex>

      {agents.length === 0 && (
        <Card mb={6}>
          <CardBody textAlign="center" py={6}>
            <Text color="orange.600" fontWeight="bold">
              No agents available! You need to create agents first before creating tasks.
            </Text>
            <Text color="gray.600" mt={2}>
              Go to the Agents section to create your first agent.
            </Text>
          </CardBody>
        </Card>
      )}

      {tasks.length === 0 ? (
        <Card>
          <CardBody textAlign="center" py={10}>
            <FiCheckSquare size={48} style={{ margin: '0 auto 16px' }} />
            <Text fontSize="lg" mb={2}>No tasks created yet</Text>
            <Text color="gray.600" mb={4}>Create tasks to assign work to your agents</Text>
            {agents.length > 0 && (
              <Button colorScheme="blue" onClick={onOpen}>Create Your First Task</Button>
            )}
          </CardBody>
        </Card>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          {tasks.map(task => (
            <Card key={task.id}>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack justify="space-between" width="100%">
                    <Badge colorScheme={getStatusColor(task.status)}>
                      {task.status}
                    </Badge>
                    <HStack spacing={1}>
                      <IconButton
                        aria-label="Edit task"
                        icon={<FiEdit />}
                        size="sm"
                        variant="ghost"
                        colorScheme="blue"
                        onClick={() => handleEdit(task)}
                      />
                      <IconButton
                        aria-label="Delete task"
                        icon={<FiTrash2 />}
                        size="sm"
                        colorScheme="red"
                        variant="ghost"
                        onClick={() => deleteTask(task.id, task.title)}
                      />
                    </HStack>
                  </HStack>
                  
                  <Box>
                    <Text fontWeight="bold" fontSize="lg">{task.title}</Text>
                    <Text color="gray.600" fontSize="sm">
                      Assigned to: {(() => {
                        if (task.assigned_agent_ids && Array.isArray(task.assigned_agent_ids) && task.assigned_agent_ids.length > 0) {
                          return getAgentName(task.assigned_agent_ids[0]);
                        } else if (task.assigned_agents && Array.isArray(task.assigned_agents) && task.assigned_agents.length > 0) {
                          return task.assigned_agents[0].name;
                        }
                        return 'None';
                      })()}
                    </Text>
                  </Box>
                  
                  <Text fontSize="sm" noOfLines={3}>{task.description}</Text>
                  
                  <Text fontSize="xs" color="gray.500">
                    Created: {new Date(task.created_at).toLocaleDateString()}
                  </Text>
                  
                  {task.updated_at !== task.created_at && (
                    <Text fontSize="xs" color="gray.500">
                      Updated: {new Date(task.updated_at).toLocaleDateString()}
                    </Text>
                  )}
                </VStack>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <Modal isOpen={isOpen} onClose={() => {
        resetForm();
        onClose();
      }} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{editingTask ? 'Edit Task' : 'Create New Task'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} mb={4}>
              <HStack justify="space-between" width="100%">
                <Text fontSize="sm" color="gray.600">
                  {isFileMode ? 'Load task configuration from JSON file or fill form manually' : 'Fill the form manually or load from a JSON file'}
                </Text>
                <HStack>
                  <Button
                    size="sm"
                    variant={isFileMode ? 'solid' : 'outline'}
                    colorScheme="green"
                    leftIcon={<FiUpload />}
                    onClick={() => setIsFileMode(!isFileMode)}
                  >
                    {isFileMode ? 'Manual Input' : 'Load from File'}
                  </Button>
                </HStack>
              </HStack>
              
              {isFileMode && (
                <FormControl>
                  <FormLabel>Upload Task JSON File</FormLabel>
                  <Input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    size="sm"
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Select a JSON file containing task configuration
                  </Text>
                </FormControl>
              )}
            </VStack>
            
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Task Title</FormLabel>
                  <Input
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Research AI market trends"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Detailed description of what the agent should accomplish"
                    rows={4}
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Assign to Agent</FormLabel>
                  <Select
                    value={formData.assigned_agent_ids?.[0] || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, assigned_agent_ids: e.target.value ? [e.target.value] : [] }))}
                    placeholder="Select an agent"
                  >
                    {agents.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.role})
                      </option>
                    ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Expected Output</FormLabel>
                  <Textarea
                    value={formData.expected_output || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, expected_output: e.target.value }))}
                    placeholder="Describe what output or deliverable is expected"
                    rows={3}
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Priority</FormLabel>
                  <Select
                    value={formData.priority || 'medium'}
                    onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as any }))}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Estimated Duration (minutes)</FormLabel>
                  <Input
                    value={formData.estimated_duration || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, estimated_duration: parseInt(e.target.value) || 0 }))}
                    placeholder="e.g., 60"
                    type="number"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Resources (comma-separated)</FormLabel>
                  <Input
                    value={formData.resources?.join(', ') || ''}
                    onChange={(e) => {
                      const resources = e.target.value.split(',').map(r => r.trim()).filter(r => r);
                      setFormData(prev => ({ ...prev, resources }));
                    }}
                    placeholder="e.g., documentation, API access, datasets"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Dependencies (comma-separated)</FormLabel>
                  <Input
                    value={formData.dependencies?.join(', ') || ''}
                    onChange={(e) => {
                      const dependencies = e.target.value.split(',').map(d => d.trim()).filter(d => d);
                      setFormData(prev => ({ ...prev, dependencies }));
                    }}
                    placeholder="e.g., task1, setup_complete"
                  />
                </FormControl>

                <HStack spacing={3} pt={4}>
                  <Button type="submit" colorScheme="blue">
                    {editingTask ? 'Update Task' : 'Create Task'}
                  </Button>
                  <Button onClick={() => {
                    resetForm();
                    onClose();
                  }}>Cancel</Button>
                </HStack>
              </VStack>
            </form>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}