import { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardBody,
  CardHeader,
  Text,
  Badge,
  VStack,
  HStack,
  Button,
  Progress,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  useToast,
  Flex,
  Divider,
} from '@chakra-ui/react';
import { FiPlay, FiPause, FiClock, FiActivity, FiAlertCircle, FiTrash2, FiSkipForward, FiX } from 'react-icons/fi';
import { apiService, Agent, Task } from '../../services/api';

// Dynamic API base to work with both localhost and WSL IP
const getApiBase = () => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return 'http://localhost:8000';
};

interface Execution {
  id: string;
  task_id: string;
  agent_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  logs: Array<{timestamp: string, message: string, level: string, agent_status?: string, needs_interaction?: boolean}>;
  output: Record<string, any>;
  duration_seconds?: string;
  work_directory?: string;
  needs_interaction?: boolean;
  agent_response?: Record<string, any>;
}

interface WorkflowExecution {
  id: string;
  pattern_id: string;
  status: string;
  started_at: string;
  progress_percentage: number;
  current_step?: string;
}

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [workflowExecutions, setWorkflowExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const cancelExecution = async (executionId: string) => {
    try {
      const response = await fetch(`${getApiBase()}/api/execution/${executionId}/cancel`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Execution cancelled',
          status: 'success',
          duration: 3000,
        });
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        throw new Error('Failed to cancel execution');
      }
    } catch (error) {
      toast({
        title: 'Failed to cancel execution',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const pauseExecution = async (executionId: string) => {
    try {
      const response = await fetch(`${getApiBase()}/api/execution/${executionId}/pause`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Execution paused',
          status: 'info',
          duration: 3000,
        });
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        throw new Error('Failed to pause execution');
      }
    } catch (error) {
      toast({
        title: 'Failed to pause execution',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const resumeExecution = async (executionId: string) => {
    try {
      const response = await fetch(`${getApiBase()}/api/execution/${executionId}/resume`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Execution resumed',
          status: 'success',
          duration: 3000,
        });
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        throw new Error('Failed to resume execution');
      }
    } catch (error) {
      toast({
        title: 'Failed to resume execution',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const abortExecution = async (executionId: string) => {
    try {
      const response = await fetch(`${getApiBase()}/api/execution/${executionId}/abort`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Execution aborted',
          status: 'warning',
          duration: 3000,
        });
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        throw new Error('Failed to abort execution');
      }
    } catch (error) {
      toast({
        title: 'Failed to abort execution',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const deleteAgent = async (agentId: string, agentName: string, force: boolean = false) => {
    try {
      const response = await fetch(`${getApiBase()}/api/agents/${agentId}?force=${force}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        const result = await response.json();
        toast({
          title: 'Agent deleted',
          description: `${agentName} deleted successfully. ${result.affected_tasks || 0} tasks affected.`,
          status: 'success',
          duration: 5000,
        });
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        const error = await response.json();
        if (error.running_executions && !force) {
          toast({
            title: 'Cannot delete agent',
            description: `Agent has ${error.running_executions} running executions. Cancel them first or use force delete.`,
            status: 'warning',
            duration: 5000,
          });
        } else {
          throw new Error(error.detail || 'Failed to delete agent');
        }
      }
    } catch (error) {
      toast({
        title: 'Failed to delete agent',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const fetchData = async () => {
    try {
      console.log('Dashboard: Fetching data...');
      const [agentsData, tasksData] = await Promise.all([
        apiService.getAgents(),
        apiService.getTasks(),
      ]);
      
      // Fetch executions
      try {
        const executionsResponse = await fetch(`${getApiBase()}/api/execution/status`);
        const executionsData = executionsResponse.ok ? await executionsResponse.json() : [];
        setExecutions(executionsData);
      } catch (e) {
        console.warn('Failed to fetch executions:', e);
        setExecutions([]);
      }
      
      // Fetch workflow executions
      try {
        const workflowResponse = await fetch(`${getApiBase()}/api/workflows/executions`);
        const workflowData = workflowResponse.ok ? await workflowResponse.json() : [];
        setWorkflowExecutions(workflowData);
      } catch (e) {
        console.warn('Failed to fetch workflow executions:', e);
        setWorkflowExecutions([]);
      }
      
      console.log('Dashboard: Data fetched successfully', { 
        agents: agentsData.length, 
        tasks: tasksData.length,
        executions: executions.length,
        workflows: workflowExecutions.length 
      });
      setAgents(agentsData);
      setTasks(tasksData);
    } catch (error) {
      console.error('Dashboard: Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {

    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeAgents = agents.filter(agent => agent.status === 'executing').length;
  const runningTasks = tasks.filter(task => task.status === 'in_progress' || task.status === 'pending').length;
  const completedTasks = tasks.filter(task => task.status === 'completed').length;

  if (loading) {
    return <Text>Loading dashboard...</Text>;
  }

  return (
    <Box>
      <Heading mb={6}>Dashboard</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6} mb={8}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Total Agents</StatLabel>
              <StatNumber>{agents.length}</StatNumber>
              <StatHelpText>{activeAgents} currently active</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Total Tasks</StatLabel>
              <StatNumber>{tasks.length}</StatNumber>
              <StatHelpText>{runningTasks} currently running</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Completed Tasks</StatLabel>
              <StatNumber>{completedTasks}</StatNumber>
              <StatHelpText>
                {tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0}% completion rate
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>System Status</StatLabel>
              <StatNumber>
                <Badge colorScheme={agents.length > 0 ? 'green' : 'gray'}>
                  {agents.length > 0 ? 'Active' : 'Idle'}
                </Badge>
              </StatNumber>
              <StatHelpText>Multi-agent system</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>Recent Agents</Heading>
            <VStack spacing={3} align="stretch">
              {agents.slice(0, 5).map(agent => (
                <HStack key={agent.id} justify="space-between" p={2} bg="gray.50" borderRadius="md">
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="bold">{agent.name}</Text>
                    <Text fontSize="sm" color="gray.600">{agent.role}</Text>
                  </VStack>
                  <HStack>
                    <Badge colorScheme={agent.status === 'executing' ? 'green' : 'gray'}>
                      {agent.status}
                    </Badge>
                    <Button
                      size="xs"
                      colorScheme="red"
                      variant="outline"
                      leftIcon={<FiTrash2 />}
                      onClick={() => deleteAgent(agent.id, agent.name)}
                    >
                      Delete
                    </Button>
                  </HStack>
                </HStack>
              ))}
              {agents.length === 0 && (
                <Text color="gray.500" textAlign="center" py={4}>
                  No agents created yet. Go to Agents section to create your first agent.
                </Text>
              )}
            </VStack>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Heading size="md" mb={4}>Recent Tasks</Heading>
            <VStack spacing={3} align="stretch">
              {tasks.slice(0, 5).map(task => (
                <HStack key={task.id} justify="space-between" p={2} bg="gray.50" borderRadius="md">
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="bold">{task.title}</Text>
                    <Text fontSize="sm" color="gray.600">{task.description}</Text>
                  </VStack>
                  <Badge 
                    colorScheme={
                      task.status === 'completed' ? 'green' :
                      task.status === 'in_progress' ? 'blue' :
                      task.status === 'failed' ? 'red' : 'gray'
                    }
                  >
                    {task.status}
                  </Badge>
                </HStack>
              ))}
              {tasks.length === 0 && (
                <Text color="gray.500" textAlign="center" py={4}>
                  No tasks created yet. Go to Tasks section to create your first task.
                </Text>
              )}
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Active Executions Monitoring */}
      {executions.length > 0 && (
        <Card mt={6}>
          <CardHeader>
            <HStack>
              <FiActivity />
              <Heading size="md">Active Executions</Heading>
              <Badge colorScheme="orange">{executions.length}</Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {executions.map(execution => {
                const agent = agents.find(a => a.id === execution.agent_id);
                const task = tasks.find(t => t.id === execution.task_id);
                const isStuck = execution.logs.length <= 1 && 
                  new Date(execution.start_time).getTime() < Date.now() - 5 * 60 * 1000; // 5 minutes
                
                return (
                  <Card key={execution.id} variant="outline" borderColor={isStuck ? "red.200" : "blue.200"}>
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack justify="space-between">
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="bold">
                              {agent?.name || 'Unknown Agent'} → {task?.title?.substring(0, 30) || 'Unknown Task'}...
                            </Text>
                            <Text fontSize="sm" color="gray.600">
                              Started: {new Date(execution.start_time).toLocaleTimeString()}
                            </Text>
                          </VStack>
                          <HStack>
                            <Badge colorScheme={
                              execution.status === 'running' ? 'green' :
                              execution.status === 'paused' ? 'yellow' :
                              execution.status === 'aborted' ? 'red' :
                              execution.status === 'cancelled' ? 'orange' : 'gray'
                            }>
                              {execution.status}
                            </Badge>
                            {isStuck && (
                              <Badge colorScheme="red">
                                <HStack spacing={1}>
                                  <FiAlertCircle />
                                  <Text>Stuck</Text>
                                </HStack>
                              </Badge>
                            )}
                            <HStack spacing={1}>
                              {execution.status === 'running' && (
                                <>
                                  <Button
                                    size="xs"
                                    colorScheme="yellow"
                                    leftIcon={<FiPause />}
                                    onClick={() => pauseExecution(execution.id)}
                                  >
                                    Pause
                                  </Button>
                                  <Button
                                    size="xs"
                                    colorScheme="red"
                                    leftIcon={<FiX />}
                                    onClick={() => abortExecution(execution.id)}
                                  >
                                    Abort
                                  </Button>
                                </>
                              )}
                              {execution.status === 'paused' && (
                                <>
                                  <Button
                                    size="xs"
                                    colorScheme="green"
                                    leftIcon={<FiPlay />}
                                    onClick={() => resumeExecution(execution.id)}
                                  >
                                    Resume
                                  </Button>
                                  <Button
                                    size="xs"
                                    colorScheme="red"
                                    leftIcon={<FiX />}
                                    onClick={() => abortExecution(execution.id)}
                                  >
                                    Abort
                                  </Button>
                                </>
                              )}
                              {(execution.status === 'running' || execution.status === 'starting') && (
                                <Button
                                  size="xs"
                                  colorScheme="orange"
                                  leftIcon={<FiSkipForward />}
                                  onClick={() => cancelExecution(execution.id)}
                                >
                                  Cancel
                                </Button>
                              )}
                            </HStack>
                          </HStack>
                        </HStack>
                        
                        {isStuck && (
                          <Alert status="warning" size="sm">
                            <AlertIcon />
                            <AlertDescription>
                              Execution appears stuck. Running for {Math.round((Date.now() - new Date(execution.start_time).getTime()) / 60000)} minutes with minimal progress.
                            </AlertDescription>
                          </Alert>
                        )}
                        
                        {/* Agent Observation Window */}
                        <Card bg="gray.50" variant="filled">
                          <CardHeader py={2}>
                            <HStack justify="space-between">
                              <Text fontSize="sm" fontWeight="bold">
                                🔍 Agent Observation Window - {agent?.name || 'Unknown Agent'}
                              </Text>
                              {execution.needs_interaction && (
                                <Badge colorScheme="yellow">
                                  <HStack spacing={1}>
                                    <FiAlertCircle />
                                    <Text>Needs Input</Text>
                                  </HStack>
                                </Badge>
                              )}
                            </HStack>
                          </CardHeader>
                          <CardBody py={2}>
                            <Accordion allowToggle>
                              <AccordionItem>
                                <AccordionButton>
                                  <Box flex="1" textAlign="left">
                                    <Text fontSize="sm">Agent Response & Analysis</Text>
                                  </Box>
                                  <AccordionIcon />
                                </AccordionButton>
                                <AccordionPanel pb={4}>
                                  {execution.agent_response && (
                                    <VStack align="stretch" spacing={3}>
                                      <Box>
                                        <Text fontSize="xs" fontWeight="bold" color="purple.600">Analysis:</Text>
                                        <Text fontSize="xs" bg="purple.50" p={2} borderRadius="md">
                                          {execution.agent_response.analysis || 'No analysis available'}
                                        </Text>
                                      </Box>
                                      <Box>
                                        <Text fontSize="xs" fontWeight="bold" color="blue.600">Approach:</Text>
                                        <Text fontSize="xs" bg="blue.50" p={2} borderRadius="md">
                                          {execution.agent_response.approach || 'No approach details'}
                                        </Text>
                                      </Box>
                                      <Box>
                                        <Text fontSize="xs" fontWeight="bold" color="green.600">Implementation:</Text>
                                        <Text fontSize="xs" bg="green.50" p={2} borderRadius="md" maxH="150px" overflowY="auto">
                                          {execution.agent_response.implementation || 'No implementation details'}
                                        </Text>
                                      </Box>
                                      <Box>
                                        <Text fontSize="xs" fontWeight="bold" color="orange.600">Results:</Text>
                                        <Text fontSize="xs" bg="orange.50" p={2} borderRadius="md">
                                          {execution.agent_response.results || 'No results available'}
                                        </Text>
                                      </Box>
                                      {execution.agent_response.recommendations && (
                                        <Box>
                                          <Text fontSize="xs" fontWeight="bold" color="red.600">Recommendations:</Text>
                                          <Text fontSize="xs" bg="red.50" p={2} borderRadius="md">
                                            {execution.agent_response.recommendations}
                                          </Text>
                                        </Box>
                                      )}
                                      {execution.work_directory && (
                                        <Box>
                                          <Text fontSize="xs" fontWeight="bold" color="gray.600">Work Directory:</Text>
                                          <Text fontSize="xs" bg="gray.100" p={1} borderRadius="md" fontFamily="mono">
                                            {execution.work_directory}
                                          </Text>
                                        </Box>
                                      )}
                                    </VStack>
                                  )}
                                  {!execution.agent_response && (
                                    <Text fontSize="xs" color="gray.500" textAlign="center" py={4}>
                                      No agent response available yet
                                    </Text>
                                  )}
                                </AccordionPanel>
                              </AccordionItem>
                              
                              <AccordionItem>
                                <AccordionButton>
                                  <Box flex="1" textAlign="left">
                                    <Text fontSize="sm">Execution Logs ({execution.logs.length} entries)</Text>
                                  </Box>
                                  <AccordionIcon />
                                </AccordionButton>
                                <AccordionPanel pb={4}>
                                  <VStack align="stretch" spacing={1} maxH="200px" overflowY="auto">
                                    {execution.logs.map((log, idx) => (
                                      <Box key={idx} fontSize="xs" p={1} borderRadius="sm" bg={log.level === 'error' ? 'red.50' : 'gray.50'}>
                                        <HStack spacing={2}>
                                          <Badge size="xs" colorScheme={log.level === 'error' ? 'red' : log.level === 'warning' ? 'yellow' : 'blue'}>
                                            {log.level}
                                          </Badge>
                                          <Text fontSize="xs" color="gray.500">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                          </Text>
                                          {log.needs_interaction && (
                                            <Badge size="xs" colorScheme="yellow">
                                              Needs Input
                                            </Badge>
                                          )}
                                        </HStack>
                                        <Text fontSize="xs" fontFamily="mono" mt={1}>
                                          {log.message}
                                        </Text>
                                      </Box>
                                    ))}
                                  </VStack>
                                </AccordionPanel>
                              </AccordionItem>
                            </Accordion>
                          </CardBody>
                        </Card>
                        
                        {Object.keys(execution.output).length > 0 && (
                          <Box>
                            <Text fontSize="sm" fontWeight="bold" mb={2}>Output:</Text>
                            <Text fontSize="xs" fontFamily="mono" bg="gray.50" p={2} borderRadius="md">
                              {JSON.stringify(execution.output, null, 2)}
                            </Text>
                          </Box>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                );
              })}
            </VStack>
          </CardBody>
        </Card>
      )}

      {/* Workflow Executions */}
      {workflowExecutions.length > 0 && (
        <Card mt={6}>
          <CardHeader>
            <HStack>
              <FiPlay />
              <Heading size="md">Active Workflows</Heading>
              <Badge colorScheme="purple">{workflowExecutions.length}</Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {workflowExecutions.map(workflow => (
                <Card key={workflow.id} variant="outline" borderColor="purple.200">
                  <CardBody>
                    <VStack align="stretch" spacing={3}>
                      <HStack justify="space-between">
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="bold">Workflow Execution</Text>
                          <Text fontSize="sm" color="gray.600">
                            ID: {workflow.id.substring(0, 8)}...
                          </Text>
                        </VStack>
                        <Badge colorScheme="purple">{workflow.status}</Badge>
                      </HStack>
                      
                      <Box>
                        <HStack justify="space-between" mb={2}>
                          <Text fontSize="sm">Progress</Text>
                          <Text fontSize="sm">{workflow.progress_percentage.toFixed(1)}%</Text>
                        </HStack>
                        <Progress value={workflow.progress_percentage} colorScheme="purple" />
                      </Box>
                      
                      {workflow.current_step && (
                        <Text fontSize="sm">
                          <strong>Current Step:</strong> {workflow.current_step}
                        </Text>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}

      {/* Warning for stuck executions */}
      {executions.some(e => e.logs.length <= 1 && new Date(e.start_time).getTime() < Date.now() - 5 * 60 * 1000) && (
        <Alert status="warning" mt={6}>
          <AlertIcon />
          <Box>
            <AlertTitle>Stuck Executions Detected!</AlertTitle>
            <AlertDescription>
              Some executions appear to be stuck. This indicates the execution engine may not be properly spawning Claude Code instances.
              Consider restarting the backend or checking the execution engine implementation.
            </AlertDescription>
          </Box>
        </Alert>
      )}
    </Box>
  );
}