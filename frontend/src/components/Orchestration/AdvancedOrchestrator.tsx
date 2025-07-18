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
  SimpleGrid,
  Flex,
  Spinner,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Checkbox,
  CheckboxGroup,
  Stack,
  Divider,
  Tag,
  TagLabel,
} from '@chakra-ui/react';
import { FiPlay, FiEye, FiSettings, FiZap, FiUsers, FiMessageSquare, FiTrendingUp, FiCpu, FiEdit, FiTrash2, FiFolder } from 'react-icons/fi';
import { apiService, Agent, Task } from '../../services/api';
import { 
  advancedOrchestrationService, 
  WorkflowPattern, 
  WorkflowExecution, 
  WorkflowAnalysis,
  AgentComm,
  WorkflowTypes,
  WorkflowTypeInfo
} from '../../services/advancedOrchestration';

export default function AdvancedOrchestrator() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workflowPatterns, setWorkflowPatterns] = useState<WorkflowPattern[]>([]);
  const [activeExecutions, setActiveExecutions] = useState<WorkflowExecution[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [communications, setCommunications] = useState<AgentComm[]>([]);
  const [workflowTypes, setWorkflowTypes] = useState<WorkflowTypes>({});
  const [analysis, setAnalysis] = useState<WorkflowAnalysis | null>(null);

  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    objective: '',
    selectedAgents: [] as string[],
    selectedTasks: [] as string[],
    workflowType: '',
    projectDirectory: '',
  });

  const [directoryValid, setDirectoryValid] = useState(false);
  const [editingPatternId, setEditingPatternId] = useState<string | null>(null);

  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isMonitorOpen, onOpen: onMonitorOpen, onClose: onMonitorClose } = useDisclosure();
  const { isOpen: isAnalyzeOpen, onOpen: onAnalyzeOpen, onClose: onAnalyzeClose } = useDisclosure();
  
  const toast = useToast();

  useEffect(() => {
    fetchData();
    fetchWorkflowTypes();
    checkDirectoryValidity(createForm.projectDirectory);
    
    // Refresh executions every 3 seconds
    const interval = setInterval(() => {
      fetchActiveExecutions();
      if (selectedExecution) {
        refreshExecutionDetails(selectedExecution.id);
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      console.log('AdvancedOrchestrator: Fetching data...');
      const [agentsData, tasksData, patternsData] = await Promise.all([
        apiService.getAgents(),
        apiService.getTasks(),
        advancedOrchestrationService.getWorkflowPatterns(),
      ]);
      console.log('AdvancedOrchestrator: Data fetched successfully', { 
        agents: agentsData.length, 
        tasks: tasksData.length, 
        patterns: Array.isArray(patternsData) ? patternsData.length : 'not array', 
        patternsData 
      });
      setAgents(agentsData);
      setTasks(tasksData);
      setWorkflowPatterns(Array.isArray(patternsData) ? patternsData : []);
    } catch (error) {
      console.error('AdvancedOrchestrator: Failed to fetch data:', error);
      setWorkflowPatterns([]); // Ensure we always have an array
    }
  };

  const fetchActiveExecutions = async () => {
    try {
      const executions = await advancedOrchestrationService.getActiveExecutions();
      setActiveExecutions(Array.isArray(executions) ? executions : []);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
      setActiveExecutions([]);
    }
  };

  const fetchWorkflowTypes = async () => {
    try {
      const types = await advancedOrchestrationService.getWorkflowTypes();
      setWorkflowTypes(types);
    } catch (error) {
      console.error('Failed to fetch workflow types:', error);
    }
  };

  const refreshExecutionDetails = async (executionId: string) => {
    try {
      const [execution, comms] = await Promise.all([
        advancedOrchestrationService.getExecutionStatus(executionId),
        advancedOrchestrationService.getAgentCommunications(executionId),
      ]);
      setSelectedExecution(execution);
      setCommunications(comms);
    } catch (error) {
      console.error('Failed to refresh execution details:', error);
    }
  };

  const analyzeWorkflow = async () => {
    if (createForm.selectedAgents.length === 0 || createForm.selectedTasks.length === 0) {
      toast({
        title: 'Please select agents and tasks for analysis',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      const result = await advancedOrchestrationService.analyzeWorkflow(
        createForm.selectedAgents,
        createForm.selectedTasks,
        createForm.objective
      );
      setAnalysis(result);
      setCreateForm(prev => ({ ...prev, workflowType: result.recommended_workflow }));
      
      toast({
        title: 'Workflow analysis completed',
        description: `Recommended: ${result.recommended_workflow}`,
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Analysis failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const createWorkflowPattern = async () => {
    if (!createForm.name || createForm.selectedAgents.length === 0 || createForm.selectedTasks.length === 0 || !createForm.projectDirectory || !directoryValid) {
      toast({
        title: 'Please fill in all required fields and ensure project directory is valid',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      // Use AI recommendation if user didn't select a workflow type
      const workflowType = createForm.workflowType || (analysis?.recommended_workflow.toUpperCase());
      
      const patternData = {
        name: createForm.name,
        description: createForm.description,
        agent_ids: createForm.selectedAgents,
        task_ids: createForm.selectedTasks,
        user_objective: createForm.objective,
        workflow_type: workflowType,
        project_directory: createForm.projectDirectory,
      };

      if (editingPatternId) {
        // Update existing pattern
        await advancedOrchestrationService.updateWorkflowPattern(editingPatternId, patternData);
        toast({
          title: 'Workflow pattern updated successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Create new pattern
        await advancedOrchestrationService.createWorkflowPattern(patternData);
        toast({
          title: 'Workflow pattern created successfully',
          status: 'success',
          duration: 3000,
        });
      }

      setCreateForm(prev => ({
        name: '',
        description: '',
        objective: '',
        selectedAgents: [],
        selectedTasks: [],
        workflowType: '',
        projectDirectory: prev.projectDirectory, // Preserve user's directory choice
      }));
      setAnalysis(null);
      setEditingPatternId(null); // Clear editing mode
      onAnalyzeClose();
      fetchData();
    } catch (error) {
      toast({
        title: editingPatternId ? 'Failed to update workflow pattern' : 'Failed to create workflow pattern',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const executeWorkflow = async (patternId: string) => {
    try {
      const execution = await advancedOrchestrationService.executeWorkflow(patternId);
      
      toast({
        title: 'Workflow execution started',
        description: `Execution ID: ${execution.id}`,
        status: 'success',
        duration: 5000,
      });

      fetchActiveExecutions();
    } catch (error) {
      toast({
        title: 'Failed to execute workflow',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const editWorkflowPattern = (patternId: string) => {
    const pattern = workflowPatterns.find(p => p.id === patternId);
    if (pattern) {
      // Set editing mode
      setEditingPatternId(patternId);
      
      // Pre-fill form with existing pattern data
      setCreateForm(prev => ({
        name: pattern.name,
        description: pattern.description,
        objective: pattern.user_objective,
        selectedAgents: pattern.agent_ids || [],
        selectedTasks: pattern.task_ids || [],
        workflowType: pattern.workflow_type,
        projectDirectory: pattern.project_directory || prev.projectDirectory, // Use pattern's directory or current choice
      }));
      onAnalyzeOpen();
    }
  };

  const deleteWorkflowPattern = async (patternId: string, force: boolean = false) => {
    const confirmMessage = force 
      ? 'Are you sure you want to FORCE DELETE this workflow pattern? This will cancel all active executions. This action cannot be undone.'
      : 'Are you sure you want to delete this workflow pattern? This action cannot be undone.';
      
    if (window.confirm(confirmMessage)) {
      try {
        await advancedOrchestrationService.deleteWorkflowPattern(patternId, force);
        toast({
          title: 'Workflow pattern deleted',
          description: force ? 'Pattern deleted and active executions cancelled' : undefined,
          status: 'success',
          duration: 3000,
        });
        fetchData(); // Refresh the patterns list
      } catch (error) {
        // Handle 409 Conflict - active executions exist
        if (error instanceof Error && error.message.includes('409')) {
          const forceDelete = window.confirm(
            'This workflow pattern has active executions that must be cancelled first.\n\n' +
            'Would you like to FORCE DELETE the pattern and cancel all active executions?\n\n' +
            'Click OK to force delete, or Cancel to abort.'
          );
          
          if (forceDelete) {
            return deleteWorkflowPattern(patternId, true); // Retry with force=true
          }
        } else {
          toast({
            title: 'Failed to delete workflow pattern',
            description: error instanceof Error ? error.message : 'Unknown error',
            status: 'error',
            duration: 5000,
          });
        }
      }
    }
  };

  // API base for project directory validation
  const getApiBase = () => {
    if (typeof window !== 'undefined') {
      const { protocol, hostname } = window.location;
      return `${protocol}//${hostname}:8000`;
    }
    return 'http://localhost:8000';
  };

  const checkDirectoryValidity = async (directory: string) => {
    try {
      const response = await fetch(`${getApiBase()}/api/project/directory-info?directory=${encodeURIComponent(directory)}`);
      const data = await response.json();
      // Empty directories are valid for workflow creation
      setDirectoryValid(data.exists);
    } catch (error) {
      setDirectoryValid(false);
    }
  };

  const getAgentName = (agentId: string) => {
    return agents.find(a => a.id === agentId)?.name || 'Unknown Agent';
  };

  const getTaskTitle = (taskId: string) => {
    return tasks.find(t => t.id === taskId)?.title || 'Unknown Task';
  };

  const getWorkflowTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'ORCHESTRATOR': return FiCpu;
      case 'PARALLEL': return FiZap;
      case 'SWARM': return FiUsers;
      case 'EVALUATOR_OPTIMIZER': return FiTrendingUp;
      default: return FiSettings;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={0}>
          <Heading>🧠 Advanced Multi-Agent Orchestration</Heading>
          <Text color="gray.600">Intelligent workflow patterns with dynamic orchestration</Text>
        </VStack>
        <HStack>
          <Button leftIcon={<FiCpu />} colorScheme="purple" onClick={onAnalyzeOpen}>
            Analyze & Create
          </Button>
          {activeExecutions.length > 0 && (
            <Button leftIcon={<FiEye />} colorScheme="green" onClick={onMonitorOpen}>
              Monitor Active ({activeExecutions.length})
            </Button>
          )}
        </HStack>
      </Flex>

      {/* Active Executions Summary */}
      {activeExecutions.length > 0 && (
        <Alert status="info" mb={6}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">{activeExecutions.length} workflow(s) currently executing</Text>
            <HStack mt={2} spacing={4}>
              {activeExecutions.map(exec => (
                <Tag key={exec.id} colorScheme="blue" cursor="pointer" onClick={() => {
                  setSelectedExecution(exec);
                  refreshExecutionDetails(exec.id);
                  onMonitorOpen();
                }}>
                  <TagLabel>{exec.status}</TagLabel>
                </Tag>
              ))}
            </HStack>
          </Box>
        </Alert>
      )}

      {/* Workflow Patterns */}
      <SimpleGrid columns={{ base: 1, lg: 2, xl: 3 }} spacing={6} mb={6}>
        {(workflowPatterns || []).map(pattern => {
          const IconComponent = getWorkflowTypeIcon(pattern.workflow_type);
          return (
            <Card key={pattern.id} _hover={{ shadow: 'md' }}>
              <CardHeader>
                <HStack justify="space-between">
                  <VStack align="start" spacing={0}>
                    <HStack>
                      <IconComponent />
                      <Text fontWeight="bold">{pattern.name}</Text>
                    </HStack>
                    <Badge colorScheme="purple">{pattern.workflow_type}</Badge>
                  </VStack>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <Text fontSize="sm" color="gray.600">{pattern.description}</Text>
                  
                  <Box>
                    <Text fontSize="xs" fontWeight="bold" mb={1}>Configuration:</Text>
                    <SimpleGrid columns={2} spacing={2}>
                      <Text fontSize="xs">
                        <strong>Agents:</strong> {pattern.agent_ids?.length || 0}
                      </Text>
                      <Text fontSize="xs">
                        <strong>Tasks:</strong> {pattern.task_ids?.length || 0}
                      </Text>
                      <Text fontSize="xs">
                        <strong>Status:</strong> {pattern.status}
                      </Text>
                      <Text fontSize="xs">
                        <strong>Created:</strong> {new Date(pattern.created_at).toLocaleDateString()}
                      </Text>
                    </SimpleGrid>
                  </Box>

                  {pattern.user_objective && (
                    <Box>
                      <Text fontSize="xs" fontWeight="bold" mb={1}>Objective:</Text>
                      <Text fontSize="xs" color="gray.600">
                        {pattern.user_objective}
                      </Text>
                    </Box>
                  )}

                  <HStack spacing={2}>
                    <Button
                      size="sm"
                      colorScheme="green"
                      leftIcon={<FiPlay />}
                      onClick={() => executeWorkflow(pattern.id)}
                    >
                      Execute
                    </Button>
                    <Button
                      size="sm"
                      leftIcon={<FiEdit />}
                      onClick={() => editWorkflowPattern(pattern.id)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      colorScheme="red"
                      variant="outline"
                      leftIcon={<FiTrash2 />}
                      onClick={() => deleteWorkflowPattern(pattern.id)}
                    >
                      Delete
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          );
        })}
      </SimpleGrid>

      {workflowPatterns.length === 0 && (
        <Card>
          <CardBody textAlign="center" py={10}>
            <FiCpu size={48} style={{ margin: '0 auto 16px' }} />
            <Text fontSize="lg" mb={2}>No advanced workflows created yet</Text>
            <Text color="gray.600" mb={4}>Create intelligent multi-agent workflows with dynamic orchestration</Text>
            <Button colorScheme="purple" onClick={onAnalyzeOpen}>Create Your First Workflow</Button>
          </CardBody>
        </Card>
      )}

      {/* Analyze & Create Modal */}
      <Modal isOpen={isAnalyzeOpen} onClose={() => {
        setEditingPatternId(null);
        onAnalyzeClose();
      }} size="6xl">
        <ModalOverlay />
        <ModalContent maxW="90vw">
          <ModalHeader>
            🧠 {editingPatternId ? 'Edit Workflow Pattern' : 'Intelligent Workflow Creation'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Tabs>
              <TabList>
                <Tab>1. Select Agents & Tasks</Tab>
                <Tab>2. Define Objective & Analyze</Tab>
                <Tab>3. Configure & Create</Tab>
              </TabList>

              <TabPanels>
                <TabPanel>
                  <VStack spacing={6}>
                    <Alert status="info" borderRadius="md">
                      <AlertIcon />
                      <VStack align="start" spacing={0} flex="1">
                        <Text fontSize="sm" fontWeight="bold">
                          Task Selection for Workflow
                        </Text>
                        <Text fontSize="xs" color="gray.600">
                          Select the tasks you want to include in this workflow. Agents are automatically determined from task assignments, and execution order is controlled by the workflow pattern type.
                        </Text>
                      </VStack>
                    </Alert>

                    <FormControl>
                      <FormLabel>Select Tasks for Workflow</FormLabel>
                      <CheckboxGroup 
                        value={createForm.selectedTasks}
                        onChange={(values) => {
                          // Automatically derive agents from selected tasks
                          const derivedAgents = values.map(taskId => {
                            const task = tasks.find(t => t.id === taskId);
                            return task?.assigned_agents?.[0]?.id || '';
                          }).filter(Boolean);
                          
                          setCreateForm(prev => ({ 
                            ...prev, 
                            selectedTasks: values as string[],
                            selectedAgents: [...new Set(derivedAgents)] // Remove duplicates
                          }));
                        }}
                      >
                        <Stack spacing={3} maxH="400px" overflowY="auto">
                          {tasks.map(task => (
                            <Checkbox key={task.id} value={task.id}>
                              <HStack spacing={3} align="start" width="100%">
                                <VStack align="start" spacing={1} flex="1">
                                  <Text fontWeight="bold">{task.title}</Text>
                                  <Text fontSize="sm" color="gray.600">{task.description}</Text>
                                  <HStack spacing={2}>
                                    {task.assigned_agents && task.assigned_agents.length > 0 ? (
                                      <>
                                        <Text fontSize="xs" color="green.600" fontWeight="bold">
                                          Agent: {task.assigned_agents[0].name}
                                        </Text>
                                        <Badge colorScheme="green" size="xs">
                                          {task.assigned_agents[0].role}
                                        </Badge>
                                      </>
                                    ) : (
                                      <Badge colorScheme="red" size="xs">
                                        ⚠️ No agent assigned
                                      </Badge>
                                    )}
                                    {task.priority && (
                                      <Badge colorScheme="purple" size="xs">
                                        {task.priority}
                                      </Badge>
                                    )}
                                  </HStack>
                                </VStack>
                              </HStack>
                            </Checkbox>
                          ))}
                        </Stack>
                      </CheckboxGroup>
                      
                      {createForm.selectedTasks.length > 0 && (
                        <Box mt={4} p={3} bg="blue.50" borderRadius="md">
                          <Text fontSize="sm" fontWeight="bold" mb={2}>Selected Tasks & Their Agents:</Text>
                          <VStack align="start" spacing={1}>
                            {createForm.selectedTasks.map(taskId => {
                              const task = tasks.find(t => t.id === taskId);
                              const agent = task?.assigned_agents?.[0];
                              return (
                                <Text key={taskId} fontSize="xs">
                                  • {task?.title || 'Unknown Task'} → {agent?.name || 'No Agent Assigned'}
                                </Text>
                              );
                            })}
                          </VStack>
                          <Text fontSize="xs" color="gray.600" mt={2}>
                            Execution order and coordination will be determined by the workflow pattern you choose.
                          </Text>
                        </Box>
                      )}
                    </FormControl>
                  </VStack>
                </TabPanel>

                <TabPanel>
                  <VStack spacing={4}>
                    <FormControl>
                      <FormLabel>Workflow Objective</FormLabel>
                      <Textarea
                        value={createForm.objective}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, objective: e.target.value }))}
                        placeholder="Describe what you want to achieve with this multi-agent workflow..."
                        rows={4}
                      />
                    </FormControl>

                    <Button 
                      colorScheme="purple" 
                      leftIcon={<FiCpu />}
                      onClick={analyzeWorkflow}
                      isDisabled={createForm.selectedAgents.length === 0 || createForm.selectedTasks.length === 0}
                    >
                      Analyze Workflow Requirements
                    </Button>

                    {analysis && (
                      <Card width="100%">
                        <CardHeader>
                          <Text fontWeight="bold">🎯 AI Analysis Results</Text>
                        </CardHeader>
                        <CardBody>
                          <VStack align="stretch" spacing={3}>
                            <HStack justify="space-between">
                              <Text fontWeight="bold">Recommended Pattern:</Text>
                              <Badge colorScheme="purple" fontSize="md" p={2}>
                                {analysis.recommended_workflow}
                              </Badge>
                            </HStack>
                            
                            <SimpleGrid columns={2} spacing={4}>
                              <Text><strong>Agents:</strong> {analysis.analysis.agent_count}</Text>
                              <Text><strong>Tasks:</strong> {analysis.analysis.task_count}</Text>
                              <Text><strong>Has Dependencies:</strong> {analysis.analysis.has_dependencies ? 'Yes' : 'No'}</Text>
                            </SimpleGrid>

                            <Text fontSize="sm" color="gray.600">
                              {workflowTypes[analysis.recommended_workflow]?.name || analysis.recommended_workflow}
                            </Text>
                          </VStack>
                        </CardBody>
                      </Card>
                    )}
                  </VStack>
                </TabPanel>

                <TabPanel>
                  <VStack spacing={4}>
                    <FormControl isRequired>
                      <FormLabel>Workflow Name</FormLabel>
                      <Input
                        value={createForm.name}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., Research & Analysis Pipeline"
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Description</FormLabel>
                      <Textarea
                        value={createForm.description}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe this workflow..."
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Workflow Type (Optional)</FormLabel>
                      {analysis && (
                        <Alert status="info" mb={3} borderRadius="md">
                          <AlertIcon />
                          <VStack align="start" spacing={0} flex="1">
                            <Text fontSize="sm" fontWeight="bold">
                              AI Recommendation: {analysis.recommended_workflow.toUpperCase()} 
                              <Badge ml={2} colorScheme="blue">Confidence: High</Badge>
                            </Text>
                            <Text fontSize="xs" color="gray.600">
                              {workflowTypes[analysis.recommended_workflow.toUpperCase()]?.description || 'Recommended workflow type'}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              Leave empty to use AI recommendation, or select below to override
                            </Text>
                          </VStack>
                        </Alert>
                      )}
                      <Select
                        value={createForm.workflowType}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, workflowType: e.target.value }))}
                        placeholder={analysis ? `Use AI recommendation (${analysis.recommended_workflow.toUpperCase()})` : "Select workflow type"}
                      >
                        {Object.entries(workflowTypes).map(([type, typeInfo]) => (
                          <option key={type} value={type}>
                            {typeInfo?.name || type}
                          </option>
                        ))}
                      </Select>
                    </FormControl>

                    <FormControl isRequired>
                      <FormLabel>Project Directory</FormLabel>
                      <Text fontSize="sm" color="gray.600" mb={3}>
                        Directory where agents will operate and produce outputs
                      </Text>
                      <VStack spacing={2} align="stretch">
                        <Input
                          value={createForm.projectDirectory}
                          onChange={(e) => {
                            const newDir = e.target.value;
                            setCreateForm(prev => ({ ...prev, projectDirectory: newDir }));
                            if (newDir) checkDirectoryValidity(newDir);
                          }}
                          placeholder="Enter project directory path..."
                          fontFamily="mono"
                          fontSize="sm"
                        />
                        <HStack justify="space-between">
                          <Text fontSize="xs" color="gray.500">
                            Agents and tasks will operate in this directory
                          </Text>
                          {directoryValid ? (
                            <Badge colorScheme="green" size="sm">Valid Directory</Badge>
                          ) : (
                            <Badge colorScheme="red" size="sm">Directory Not Found</Badge>
                          )}
                        </HStack>
                      </VStack>
                    </FormControl>

                    <HStack spacing={3} pt={4}>
                      <Button colorScheme="purple" onClick={createWorkflowPattern}>
                        {editingPatternId ? 'Update Workflow Pattern' : 'Create Workflow Pattern'}
                      </Button>
                      <Button onClick={() => {
                        setCreateForm(prev => ({
                          name: '',
                          description: '',
                          objective: '',
                          selectedAgents: [],
                          selectedTasks: [],
                          workflowType: '',
                          projectDirectory: prev.projectDirectory, // Preserve user's directory choice
                        }));
                        setAnalysis(null);
                        setEditingPatternId(null); // Clear editing mode
                        onAnalyzeClose();
                      }}>Cancel</Button>
                    </HStack>
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Monitor Execution Modal */}
      <Modal isOpen={isMonitorOpen} onClose={onMonitorClose} size="6xl">
        <ModalOverlay />
        <ModalContent maxW="95vw">
          <ModalHeader>
            📊 Real-Time Workflow Monitoring
            {selectedExecution && (
              <Badge ml={3} colorScheme={getStatusColor(selectedExecution.status)}>
                {selectedExecution.status}
              </Badge>
            )}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedExecution ? (
              <VStack spacing={6}>
                {/* Execution Summary */}
                <Card width="100%">
                  <CardBody>
                    <VStack spacing={3}>
                      <HStack justify="space-between" width="100%">
                        <Text fontWeight="bold">Execution Summary</Text>
                        <Badge colorScheme={getStatusColor(selectedExecution.status)}>
                          {selectedExecution.status}
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        ID: {selectedExecution.id}
                      </Text>
                      <Text fontSize="sm" color="gray.600">
                        Started: {selectedExecution.started_at ? new Date(selectedExecution.started_at).toLocaleString() : 'N/A'}
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>

                <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} width="100%">
                  {/* Agent Communications */}
                  <Card>
                    <CardHeader>
                      <HStack>
                        <FiMessageSquare />
                        <Text fontWeight="bold">Agent Communications</Text>
                      </HStack>
                    </CardHeader>
                    <CardBody maxH="400px" overflowY="auto">
                      <VStack spacing={3} align="stretch">
                        {communications.map(comm => (
                          <Box 
                            key={comm.id} 
                            p={3} 
                            border="1px" 
                            borderColor="blue.200" 
                            borderRadius="md" 
                            bg={comm.message_type === 'error' ? 'red.50' : 'blue.50'}
                          >
                            <HStack justify="space-between" mb={2}>
                              <Text fontSize="sm" fontWeight="bold">
                                {getAgentName(comm.from_agent_id)} → {getAgentName(comm.to_agent_id)}
                              </Text>
                              <Badge colorScheme={comm.message_type === 'error' ? 'red' : 'blue'}>
                                {comm.message_type}
                              </Badge>
                            </HStack>
                            <Text fontSize="sm">{comm.message}</Text>
                            <Text fontSize="xs" color="gray.500">
                              {new Date(comm.timestamp).toLocaleTimeString()}
                            </Text>
                          </Box>
                        ))}
                        {communications.length === 0 && (
                          <Text color="gray.500" textAlign="center">
                            No communications yet
                          </Text>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>

                  {/* Task Status */}
                  <Card>
                    <CardHeader>
                      <Text fontWeight="bold">Task Execution Status</Text>
                    </CardHeader>
                    <CardBody maxH="400px" overflowY="auto">
                      <VStack spacing={3} align="stretch">
                        <HStack justify="space-between">
                          <Text fontSize="sm">Completed:</Text>
                          <Badge colorScheme="green">{selectedExecution.completed_tasks.length}</Badge>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm">Active Agents:</Text>
                          <Badge colorScheme="blue">{selectedExecution.active_agents.length}</Badge>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm">Failed Tasks:</Text>
                          <Badge colorScheme="red">{selectedExecution.failed_tasks.length}</Badge>
                        </HStack>
                        
                        <Divider />
                        
                        {selectedExecution.active_agents.length > 0 && (
                          <Box>
                            <Text fontSize="sm" fontWeight="bold" mb={2}>Currently Active:</Text>
                            {selectedExecution.active_agents.map(agentId => (
                              <Tag key={agentId} mr={2} mb={1} colorScheme="blue">
                                {getAgentName(agentId)}
                              </Tag>
                            ))}
                          </Box>
                        )}
                      </VStack>
                    </CardBody>
                  </Card>
                </SimpleGrid>
              </VStack>
            ) : (
              <VStack spacing={4}>
                <Text>Select an execution to monitor:</Text>
                <SimpleGrid columns={2} spacing={4} width="100%">
                  {(activeExecutions || []).map(execution => (
                    <Card 
                      key={execution.id} 
                      cursor="pointer" 
                      onClick={() => {
                        setSelectedExecution(execution);
                        refreshExecutionDetails(execution.id);
                      }}
                      _hover={{ shadow: 'md' }}
                    >
                      <CardBody>
                        <VStack align="start" spacing={2}>
                          <HStack justify="space-between" width="100%">
                            <Text fontWeight="bold" fontSize="sm">
                              Execution {execution.id.slice(0, 8)}...
                            </Text>
                            <Badge colorScheme={getStatusColor(execution.status)}>
                              {execution.status}
                            </Badge>
                          </HStack>
                          <Text fontSize="xs" color="gray.600">
                            Started: {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'N/A'}
                          </Text>
                        </VStack>
                      </CardBody>
                    </Card>
                  ))}
                </SimpleGrid>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}