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
import { FiPlus, FiPlay, FiCheckSquare } from 'react-icons/fi';
import { apiService, Agent, Task, CreateTaskData } from '../../services/api';

export default function TaskManager() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
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
        agent_id: '',
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
        <Button 
          leftIcon={<FiPlus />} 
          colorScheme="blue" 
          onClick={onOpen}
          isDisabled={agents.length === 0}
        >
          Create Task
        </Button>
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
                  </HStack>
                  
                  <Box>
                    <Text fontWeight="bold" fontSize="lg">{task.title}</Text>
                    <Text color="gray.600" fontSize="sm">
                      Assigned to: {getAgentName(task.agent_id)}
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
                    value={formData.agent_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, agent_id: e.target.value }))}
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