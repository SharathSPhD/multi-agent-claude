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
import { FiPlus, FiPlay, FiCheckSquare, FiTrash2, FiUpload } from 'react-icons/fi';
import { apiService, Agent, Task, CreateTaskData } from '../../services/api';

export default function TaskManager() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [formData, setFormData] = useState<CreateTaskData>({
    title: '',
    description: '',
    assigned_agent_ids: [],
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
    const directory = '/mnt/e/Development/mcp_a2a/project_selfdevelop'; // Get from project settings
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
    
    if (!formData.title || !formData.description || !formData.agent_id) {
      toast({
        title: 'Please fill in all required fields',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      await apiService.createTask(formData);
      toast({
        title: 'Task created successfully',
        status: 'success',
        duration: 3000,
      });
      
      setFormData({
        title: '',
        description: '',
        assigned_agent_ids: [],
      });
      onClose();
      fetchData();
    } catch (error) {
      toast({
        title: 'Error creating task',
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
            leftIcon={<FiUpload />} 
            colorScheme="green" 
            variant="outline"
            onClick={loadTasksFromFiles}
            isLoading={loadingFiles}
          >
            Load from Files
          </Button>
          {tasks.length > 0 && (
            <Button 
              leftIcon={<FiTrash2 />} 
              colorScheme="red" 
              variant="outline"
              onClick={() => deleteAllTasks()}
            >
              Delete All Tasks
            </Button>
          )}
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue" 
            onClick={onOpen}
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
                      {task.status === 'pending' && (
                        <IconButton
                          aria-label="Execute task"
                          icon={<FiPlay />}
                          size="sm"
                          colorScheme="green"
                          variant="ghost"
                          onClick={() => handleExecute(task.id)}
                        />
                      )}
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

      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Task</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
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

                <HStack spacing={3} pt={4}>
                  <Button type="submit" colorScheme="blue">Create Task</Button>
                  <Button onClick={onClose}>Cancel</Button>
                </HStack>
              </VStack>
            </form>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}