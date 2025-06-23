import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  HStack,
  Tag,
  TagLabel,
  TagCloseButton,
  IconButton,
  Alert,
  AlertIcon,
  useToast,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Divider,
  Grid,
  GridItem,
  Switch,
  NumberInput,
  NumberInputField,
  Select
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import { Agent, CreateAgentData, AgentUpdate } from '../../types/api';
import { useAppDispatch } from '../../store/hooks';
import { createAgent, updateAgent } from '../../store/slices/agentsSlice';

interface AgentFormProps {
  agent?: Agent;
  onSubmit?: (agent: Agent) => void;
  onCancel?: () => void;
}

const AgentForm: React.FC<AgentFormProps> = ({ agent, onSubmit, onCancel }) => {
  const dispatch = useAppDispatch();
  const toast = useToast();
  
  const [formData, setFormData] = useState<CreateAgentData>({
    name: '',
    role: '',
    description: '',
    system_prompt: '',
    capabilities: [],
    tools: [],
    objectives: [],
    constraints: [],
    memory_settings: {
      persist_history: true,
      max_memory_size: 1000,
      context_window: 4000
    },
    execution_settings: {
      max_concurrent_tasks: 1,
      timeout_seconds: 3600,
      retry_attempts: 3
    }
  });
  
  const [newCapability, setNewCapability] = useState('');
  const [newTool, setNewTool] = useState('');
  const [newObjective, setNewObjective] = useState('');
  const [newConstraint, setNewConstraint] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  // Pre-populate form if editing existing agent
  useEffect(() => {
    if (agent) {
      setFormData({
        name: agent.name,
        role: agent.role,
        description: agent.description || '',
        system_prompt: agent.system_prompt,
        capabilities: agent.capabilities,
        tools: agent.tools,
        objectives: agent.objectives,
        constraints: agent.constraints,
        memory_settings: agent.memory_settings,
        execution_settings: agent.execution_settings
      });
    }
  }, [agent]);

  const validateForm = (): boolean => {
    const newErrors: string[] = [];
    
    if (!formData.name.trim()) newErrors.push('Agent name is required');
    if (!formData.role.trim()) newErrors.push('Agent role is required');
    if (!formData.system_prompt.trim()) newErrors.push('System prompt is required');
    if (formData.system_prompt.length < 50) newErrors.push('System prompt must be at least 50 characters');
    if (formData.capabilities.length === 0) newErrors.push('At least one capability is required');
    if (formData.objectives.length === 0) newErrors.push('At least one objective is required');
    
    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the form errors before submitting',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      let result;
      if (agent) {
        // Update existing agent
        result = await dispatch(updateAgent({ 
          id: agent.id, 
          updates: formData as AgentUpdate 
        })).unwrap();
      } else {
        // Create new agent
        result = await dispatch(createAgent(formData)).unwrap();
      }
      
      toast({
        title: agent ? 'Agent Updated' : 'Agent Created',
        description: `Agent "${result.name}" has been ${agent ? 'updated' : 'created'} successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true
      });
      
      if (onSubmit) {
        onSubmit(result);
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save agent',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  const addItem = (type: 'capabilities' | 'tools' | 'objectives' | 'constraints', value: string) => {
    if (!value.trim()) return;
    
    setFormData(prev => ({
      ...prev,
      [type]: [...prev[type], value.trim()]
    }));
    
    // Clear input
    switch (type) {
      case 'capabilities': setNewCapability(''); break;
      case 'tools': setNewTool(''); break;
      case 'objectives': setNewObjective(''); break;
      case 'constraints': setNewConstraint(''); break;
    }
  };

  const removeItem = (type: 'capabilities' | 'tools' | 'objectives' | 'constraints', index: number) => {
    setFormData(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  const renderTagInput = (
    type: 'capabilities' | 'tools' | 'objectives' | 'constraints',
    label: string,
    value: string,
    setValue: (value: string) => void,
    placeholder: string
  ) => (
    <FormControl>
      <FormLabel>{label}</FormLabel>
      <HStack mb={2}>
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addItem(type, value);
            }
          }}
        />
        <IconButton
          aria-label={`Add ${label.toLowerCase()}`}
          icon={<AddIcon />}
          onClick={() => addItem(type, value)}
          isDisabled={!value.trim()}
        />
      </HStack>
      <Box>
        {formData[type].map((item, index) => (
          <Tag key={index} size="md" mr={2} mb={2} variant="solid" colorScheme="blue">
            <TagLabel>{item}</TagLabel>
            <TagCloseButton onClick={() => removeItem(type, index)} />
          </Tag>
        ))}
      </Box>
    </FormControl>
  );

  return (
    <Card maxW="4xl" mx="auto">
      <CardHeader>
        <Heading size="lg">
          {agent ? 'Edit Agent' : 'Create New Agent'}
        </Heading>
      </CardHeader>
      
      <CardBody>
        {errors.length > 0 && (
          <Alert status="error" mb={4}>
            <AlertIcon />
            <Box>
              {errors.map((error, index) => (
                <div key={index}>{error}</div>
              ))}
            </Box>
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <VStack spacing={6} align="stretch">
            {/* Basic Information */}
            <Grid templateColumns="repeat(2, 1fr)" gap={4}>
              <GridItem>
                <FormControl isRequired>
                  <FormLabel>Agent Name</FormLabel>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Data Analysis Expert"
                  />
                </FormControl>
              </GridItem>
              
              <GridItem>
                <FormControl isRequired>
                  <FormLabel>Role</FormLabel>
                  <Select
                    value={formData.role}
                    onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                    placeholder="Select agent role"
                  >
                    <option value="domain_expert">Domain Expert</option>
                    <option value="software_developer">Software Developer</option>
                    <option value="data_analyst">Data Analyst</option>
                    <option value="researcher">Researcher</option>
                    <option value="coordinator">Coordinator</option>
                    <option value="specialist">Specialist</option>
                  </Select>
                </FormControl>
              </GridItem>
            </Grid>
            
            <FormControl>
              <FormLabel>Description</FormLabel>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of the agent's purpose and expertise"
                rows={3}
              />
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>System Prompt</FormLabel>
              <Textarea
                value={formData.system_prompt}
                onChange={(e) => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                placeholder="Detailed instructions that define the agent's behavior, expertise, and response style..."
                rows={8}
              />
            </FormControl>
            
            <Divider />
            
            {/* Capabilities and Tools */}
            {renderTagInput(
              'capabilities',
              'Capabilities',
              newCapability,
              setNewCapability,
              'e.g., data_analysis, machine_learning, research'
            )}
            
            {renderTagInput(
              'tools',
              'Available Tools',
              newTool,
              setNewTool,
              'e.g., mcp-memory, mcp-filesystem, python_interpreter'
            )}
            
            {renderTagInput(
              'objectives',
              'Primary Objectives',
              newObjective,
              setNewObjective,
              'e.g., Analyze data patterns, Generate insights'
            )}
            
            {renderTagInput(
              'constraints',
              'Constraints & Limitations',
              newConstraint,
              setNewConstraint,
              'e.g., No access to external APIs, Read-only file access'
            )}
            
            <Divider />
            
            {/* Memory Settings */}
            <Box>
              <Heading size="md" mb={4}>Memory Settings</Heading>
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <GridItem>
                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Persist History</FormLabel>
                    <Switch
                      isChecked={formData.memory_settings.persist_history}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        memory_settings: {
                          ...prev.memory_settings,
                          persist_history: e.target.checked
                        }
                      }))}
                    />
                  </FormControl>
                </GridItem>
                
                <GridItem>
                  <FormControl>
                    <FormLabel>Max Memory Size</FormLabel>
                    <NumberInput
                      value={formData.memory_settings.max_memory_size}
                      onChange={(_, value) => setFormData(prev => ({
                        ...prev,
                        memory_settings: {
                          ...prev.memory_settings,
                          max_memory_size: value || 1000
                        }
                      }))}
                      min={100}
                      max={10000}
                    >
                      <NumberInputField />
                    </NumberInput>
                  </FormControl>
                </GridItem>
                
                <GridItem>
                  <FormControl>
                    <FormLabel>Context Window</FormLabel>
                    <NumberInput
                      value={formData.memory_settings.context_window}
                      onChange={(_, value) => setFormData(prev => ({
                        ...prev,
                        memory_settings: {
                          ...prev.memory_settings,
                          context_window: value || 4000
                        }
                      }))}
                      min={1000}
                      max={20000}
                    >
                      <NumberInputField />
                    </NumberInput>
                  </FormControl>
                </GridItem>
              </Grid>
            </Box>
            
            {/* Execution Settings */}
            <Box>
              <Heading size="md" mb={4}>Execution Settings</Heading>
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <GridItem>
                  <FormControl>
                    <FormLabel>Max Concurrent Tasks</FormLabel>
                    <NumberInput
                      value={formData.execution_settings.max_concurrent_tasks}
                      onChange={(_, value) => setFormData(prev => ({
                        ...prev,
                        execution_settings: {
                          ...prev.execution_settings,
                          max_concurrent_tasks: value || 1
                        }
                      }))}
                      min={1}
                      max={10}
                    >
                      <NumberInputField />
                    </NumberInput>
                  </FormControl>
                </GridItem>
                
                <GridItem>
                  <FormControl>
                    <FormLabel>Timeout (seconds)</FormLabel>
                    <NumberInput
                      value={formData.execution_settings.timeout_seconds}
                      onChange={(_, value) => setFormData(prev => ({
                        ...prev,
                        execution_settings: {
                          ...prev.execution_settings,
                          timeout_seconds: value || 3600
                        }
                      }))}
                      min={60}
                      max={86400}
                    >
                      <NumberInputField />
                    </NumberInput>
                  </FormControl>
                </GridItem>
                
                <GridItem>
                  <FormControl>
                    <FormLabel>Retry Attempts</FormLabel>
                    <NumberInput
                      value={formData.execution_settings.retry_attempts}
                      onChange={(_, value) => setFormData(prev => ({
                        ...prev,
                        execution_settings: {
                          ...prev.execution_settings,
                          retry_attempts: value || 3
                        }
                      }))}
                      min={0}
                      max={10}
                    >
                      <NumberInputField />
                    </NumberInput>
                  </FormControl>
                </GridItem>
              </Grid>
            </Box>
            
            {/* Action Buttons */}
            <HStack justify="flex-end" spacing={4}>
              {onCancel && (
                <Button variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
              <Button
                type="submit"
                colorScheme="blue"
                isLoading={isLoading}
                loadingText={agent ? 'Updating...' : 'Creating...'}
              >
                {agent ? 'Update Agent' : 'Create Agent'}
              </Button>
            </HStack>
          </VStack>
        </form>
      </CardBody>
    </Card>
  );
};

export default AgentForm;