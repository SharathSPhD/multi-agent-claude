import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Button,
  Card,
  CardBody,
  CardHeader,
  VStack,
  HStack,
  Text,
  Badge,
  Progress,
  Alert,
  AlertIcon,
  Select,
  Textarea,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Input,
  Divider,
  SimpleGrid,
  Flex,
  Spinner,
} from '@chakra-ui/react';
import { FiPlay, FiPause, FiSquare, FiMessageSquare, FiEye } from 'react-icons/fi';
import { apiService, Agent, Task } from '../../services/api';

interface WorkflowStep {
  id: string;
  agent_id: string;
  task_id: string;
  order: number;
  dependencies?: string[];
}

interface MultiAgentWorkflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  status: 'idle' | 'running' | 'completed' | 'failed';
  created_at: string;
}

interface AgentCommunication {
  id: string;
  from_agent: string;
  to_agent: string;
  message: string;
  timestamp: string;
  workflow_id: string;
}

interface TaskExecution {
  id: string;
  task_id: string;
  agent_id: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  output?: string;
  logs: string[];
  started_at?: string;
  completed_at?: string;
}

export default function MultiAgentOrchestrator() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workflows, setWorkflows] = useState<MultiAgentWorkflow[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<MultiAgentWorkflow | null>(null);
  const [communications, setCommunications] = useState<AgentCommunication[]>([]);
  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [workflowForm, setWorkflowForm] = useState({
    name: '',
    description: '',
    steps: [] as WorkflowStep[]
  });

  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isMonitorOpen, onOpen: onMonitorOpen, onClose: onMonitorClose } = useDisclosure();
  const toast = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [agentsData, tasksData] = await Promise.all([
        apiService.getAgents(),
        apiService.getTasks(),
      ]);
      setAgents(agentsData);
      setTasks(tasksData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  const addWorkflowStep = () => {
    const newStep: WorkflowStep = {
      id: Date.now().toString(),
      agent_id: '',
      task_id: '',
      order: workflowForm.steps.length + 1,
    };
    setWorkflowForm(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }));
  };

  const updateWorkflowStep = (stepId: string, field: keyof WorkflowStep, value: any) => {
    setWorkflowForm(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, [field]: value } : step
      )
    }));
  };

  const removeWorkflowStep = (stepId: string) => {
    setWorkflowForm(prev => ({
      ...prev,
      steps: prev.steps.filter(step => step.id !== stepId)
    }));
  };

  const createWorkflow = () => {
    if (!workflowForm.name || workflowForm.steps.length === 0) {
      toast({
        title: 'Please provide workflow name and at least one step',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    const newWorkflow: MultiAgentWorkflow = {
      id: Date.now().toString(),
      name: workflowForm.name,
      description: workflowForm.description,
      steps: workflowForm.steps,
      status: 'idle',
      created_at: new Date().toISOString(),
    };

    setWorkflows(prev => [...prev, newWorkflow]);
    setWorkflowForm({ name: '', description: '', steps: [] });
    onCreateClose();
    
    toast({
      title: 'Workflow created successfully',
      status: 'success',
      duration: 3000,
    });
  };

  const startWorkflow = async (workflow: MultiAgentWorkflow) => {
    setActiveWorkflow({ ...workflow, status: 'running' });
    setExecutions([]);
    setCommunications([]);
    
    toast({
      title: 'Multi-agent workflow started',
      status: 'info',
      duration: 3000,
    });

    // Simulate workflow execution
    for (const step of workflow.steps) {
      const execution: TaskExecution = {
        id: Date.now().toString(),
        task_id: step.task_id,
        agent_id: step.agent_id,
        status: 'executing',
        logs: [],
        started_at: new Date().toISOString(),
      };
      
      setExecutions(prev => [...prev, execution]);
      
      // Simulate task execution
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update execution status
      const completedExecution = {
        ...execution,
        status: 'completed' as const,
        output: `Task completed by ${agents.find(a => a.id === step.agent_id)?.name}`,
        completed_at: new Date().toISOString(),
        logs: [
          `Started task execution`,
          `Processing data...`,
          `Task completed successfully`
        ]
      };
      
      setExecutions(prev => prev.map(exec => 
        exec.id === execution.id ? completedExecution : exec
      ));

      // Simulate agent communication
      if (workflow.steps.length > 1) {
        const comm: AgentCommunication = {
          id: Date.now().toString(),
          from_agent: step.agent_id,
          to_agent: workflow.steps[(step.order % workflow.steps.length)]?.agent_id || '',
          message: `Completed task: ${tasks.find(t => t.id === step.task_id)?.title}`,
          timestamp: new Date().toISOString(),
          workflow_id: workflow.id,
        };
        setCommunications(prev => [...prev, comm]);
      }
    }

    setActiveWorkflow(prev => prev ? { ...prev, status: 'completed' } : null);
    toast({
      title: 'Multi-agent workflow completed',
      status: 'success',
      duration: 5000,
    });
  };

  const getAgentName = (agentId: string) => {
    return agents.find(a => a.id === agentId)?.name || 'Unknown Agent';
  };

  const getTaskTitle = (taskId: string) => {
    return tasks.find(t => t.id === taskId)?.title || 'Unknown Task';
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading>Multi-Agent Orchestration</Heading>
        <HStack>
          <Button leftIcon={<FiPlay />} colorScheme="blue" onClick={onCreateOpen}>
            Create Workflow
          </Button>
          {activeWorkflow && (
            <Button leftIcon={<FiEye />} colorScheme="green" onClick={onMonitorOpen}>
              Monitor Active Workflow
            </Button>
          )}
        </HStack>
      </Flex>

      {/* Workflow List */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={6}>
        {workflows.map(workflow => (
          <Card key={workflow.id}>
            <CardHeader>
              <HStack justify="space-between">
                <VStack align="start" spacing={0}>
                  <Text fontWeight="bold">{workflow.name}</Text>
                  <Text fontSize="sm" color="gray.600">{workflow.description}</Text>
                </VStack>
                <Badge colorScheme={
                  workflow.status === 'completed' ? 'green' :
                  workflow.status === 'running' ? 'blue' :
                  workflow.status === 'failed' ? 'red' : 'gray'
                }>
                  {workflow.status}
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack align="stretch" spacing={2}>
                <Text fontSize="sm" fontWeight="bold">Steps ({workflow.steps.length}):</Text>
                {workflow.steps.map((step, idx) => (
                  <HStack key={step.id} fontSize="sm" p={2} bg="gray.50" borderRadius="md">
                    <Text>{idx + 1}.</Text>
                    <Text color="blue.600">{getAgentName(step.agent_id)}</Text>
                    <Text>→</Text>
                    <Text>{getTaskTitle(step.task_id)}</Text>
                  </HStack>
                ))}
                <Button
                  size="sm"
                  colorScheme="green"
                  leftIcon={<FiPlay />}
                  onClick={() => startWorkflow(workflow)}
                  isDisabled={workflow.status === 'running'}
                >
                  {workflow.status === 'running' ? 'Running...' : 'Start Workflow'}
                </Button>
              </VStack>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>

      {workflows.length === 0 && (
        <Card>
          <CardBody textAlign="center" py={10}>
            <Text fontSize="lg" mb={2}>No multi-agent workflows created yet</Text>
            <Text color="gray.600" mb={4}>Create workflows to orchestrate multiple agents working together</Text>
            <Button colorScheme="blue" onClick={onCreateOpen}>Create Your First Workflow</Button>
          </CardBody>
        </Card>
      )}

      {/* Active Workflow Status */}
      {activeWorkflow && (
        <Card mb={6}>
          <CardHeader>
            <HStack justify="space-between">
              <Text fontWeight="bold">Active: {activeWorkflow.name}</Text>
              <HStack>
                <Badge colorScheme={
                  activeWorkflow.status === 'completed' ? 'green' :
                  activeWorkflow.status === 'running' ? 'blue' : 'gray'
                }>
                  {activeWorkflow.status}
                </Badge>
                {activeWorkflow.status === 'running' && <Spinner size="sm" />}
              </HStack>
            </HStack>
          </CardHeader>
          <CardBody>
            <Progress 
              value={
                activeWorkflow.status === 'completed' ? 100 :
                activeWorkflow.status === 'running' ? 
                  (executions.filter(e => e.status === 'completed').length / activeWorkflow.steps.length) * 100 : 0
              }
              colorScheme="blue"
              mb={4}
            />
            <Text fontSize="sm" color="gray.600">
              {executions.filter(e => e.status === 'completed').length} of {activeWorkflow.steps.length} steps completed
            </Text>
          </CardBody>
        </Card>
      )}

      {/* Create Workflow Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create Multi-Agent Workflow</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Workflow Name</FormLabel>
                <Input
                  value={workflowForm.name}
                  onChange={(e) => setWorkflowForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Research and Analysis Pipeline"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={workflowForm.description}
                  onChange={(e) => setWorkflowForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this workflow accomplishes"
                />
              </FormControl>

              <Box width="100%">
                <HStack justify="space-between" mb={3}>
                  <Text fontWeight="bold">Workflow Steps</Text>
                  <Button size="sm" onClick={addWorkflowStep}>Add Step</Button>
                </HStack>
                
                {workflowForm.steps.map((step, idx) => (
                  <Card key={step.id} mb={3}>
                    <CardBody>
                      <HStack justify="space-between" mb={2}>
                        <Text fontWeight="bold">Step {idx + 1}</Text>
                        <Button size="xs" colorScheme="red" onClick={() => removeWorkflowStep(step.id)}>
                          Remove
                        </Button>
                      </HStack>
                      
                      <SimpleGrid columns={2} spacing={3}>
                        <FormControl>
                          <FormLabel fontSize="sm">Agent</FormLabel>
                          <Select
                            value={step.agent_id}
                            onChange={(e) => updateWorkflowStep(step.id, 'agent_id', e.target.value)}
                            placeholder="Select agent"
                          >
                            {agents.map(agent => (
                              <option key={agent.id} value={agent.id}>
                                {agent.name} ({agent.role})
                              </option>
                            ))}
                          </Select>
                        </FormControl>
                        
                        <FormControl>
                          <FormLabel fontSize="sm">Task</FormLabel>
                          <Select
                            value={step.task_id}
                            onChange={(e) => updateWorkflowStep(step.id, 'task_id', e.target.value)}
                            placeholder="Select task"
                          >
                            {tasks.map(task => (
                              <option key={task.id} value={task.id}>
                                {task.title}
                              </option>
                            ))}
                          </Select>
                        </FormControl>
                      </SimpleGrid>
                    </CardBody>
                  </Card>
                ))}
              </Box>

              <HStack spacing={3} pt={4}>
                <Button colorScheme="blue" onClick={createWorkflow}>Create Workflow</Button>
                <Button onClick={onCreateClose}>Cancel</Button>
              </HStack>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Monitor Workflow Modal */}
      <Modal isOpen={isMonitorOpen} onClose={onMonitorClose} size="6xl">
        <ModalOverlay />
        <ModalContent maxW="90vw">
          <ModalHeader>Monitor Multi-Agent Workflow</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
              {/* Task Executions */}
              <Card>
                <CardHeader>
                  <Text fontWeight="bold">Task Executions</Text>
                </CardHeader>
                <CardBody maxH="400px" overflowY="auto">
                  <VStack spacing={3} align="stretch">
                    {executions.map(execution => (
                      <Box key={execution.id} p={3} border="1px" borderColor="gray.200" borderRadius="md">
                        <HStack justify="space-between" mb={2}>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="bold" fontSize="sm">
                              {getAgentName(execution.agent_id)} → {getTaskTitle(execution.task_id)}
                            </Text>
                            <Text fontSize="xs" color="gray.600">
                              {execution.started_at && new Date(execution.started_at).toLocaleTimeString()}
                            </Text>
                          </VStack>
                          <Badge colorScheme={
                            execution.status === 'completed' ? 'green' :
                            execution.status === 'executing' ? 'blue' :
                            execution.status === 'failed' ? 'red' : 'gray'
                          }>
                            {execution.status}
                          </Badge>
                        </HStack>
                        
                        {execution.output && (
                          <Text fontSize="sm" bg="green.50" p={2} borderRadius="md" mb={2}>
                            Output: {execution.output}
                          </Text>
                        )}
                        
                        {execution.logs.length > 0 && (
                          <Box>
                            <Text fontSize="xs" fontWeight="bold" mb={1}>Logs:</Text>
                            {execution.logs.map((log, idx) => (
                              <Text key={idx} fontSize="xs" color="gray.600">• {log}</Text>
                            ))}
                          </Box>
                        )}
                      </Box>
                    ))}
                  </VStack>
                </CardBody>
              </Card>

              {/* Agent Communications */}
              <Card>
                <CardHeader>
                  <Text fontWeight="bold">Agent Communications</Text>
                </CardHeader>
                <CardBody maxH="400px" overflowY="auto">
                  <VStack spacing={3} align="stretch">
                    {communications.map(comm => (
                      <Box key={comm.id} p={3} border="1px" borderColor="blue.200" borderRadius="md" bg="blue.50">
                        <HStack justify="space-between" mb={2}>
                          <Text fontSize="sm" fontWeight="bold">
                            {getAgentName(comm.from_agent)} → {getAgentName(comm.to_agent)}
                          </Text>
                          <Text fontSize="xs" color="gray.600">
                            {new Date(comm.timestamp).toLocaleTimeString()}
                          </Text>
                        </HStack>
                        <Text fontSize="sm">{comm.message}</Text>
                      </Box>
                    ))}
                    {communications.length === 0 && (
                      <Text color="gray.500" textAlign="center" py={4}>
                        No agent communications yet
                      </Text>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </SimpleGrid>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}