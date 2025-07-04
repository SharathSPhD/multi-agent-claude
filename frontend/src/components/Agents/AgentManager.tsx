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
  useToast,
  IconButton,
  Flex,
} from '@chakra-ui/react';
import { FiPlus, FiTrash2, FiUser, FiUpload, FiEdit } from 'react-icons/fi';
import { apiService, Agent, CreateAgentData } from '../../services/api';

export default function AgentManager() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [isFileMode, setIsFileMode] = useState(false);
  const [formData, setFormData] = useState<CreateAgentData>({
    name: '',
    role: '',
    description: '',
    system_prompt: '',
    capabilities: [],
    tools: [],
    objectives: [],
    constraints: [],
  });
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const fetchAgents = async () => {
    try {
      const data = await apiService.getAgents();
      setAgents(data);
    } catch (error) {
      toast({
        title: 'Error fetching agents',
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

  const loadAgentsFromFiles = async () => {
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
        throw new Error('Failed to load agents from files');
      }
      
      const results = await response.json();
      
      toast({
        title: 'Agents loaded successfully',
        description: `Loaded ${results.agents_loaded} agents from ${results.files_processed.length} files`,
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

      // Refresh agents list
      fetchAgents();
      
    } catch (error) {
      toast({
        title: 'Error loading agents',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000
      });
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.role || !formData.description || !formData.system_prompt) {
      toast({
        title: 'Please fill in all required fields',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      if (editingAgent) {
        // Update existing agent
        await apiService.updateAgent(editingAgent.id, formData);
        toast({
          title: 'Agent updated successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Create new agent
        await apiService.createAgent(formData);
        toast({
          title: 'Agent created successfully',
          status: 'success',
          duration: 3000,
        });
      }
      
      resetForm();
      onClose();
      fetchAgents();
    } catch (error) {
      toast({
        title: editingAgent ? 'Error updating agent' : 'Error creating agent',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      await apiService.deleteAgent(id);
      toast({
        title: 'Agent deleted successfully',
        status: 'success',
        duration: 3000,
      });
      fetchAgents();
    } catch (error) {
      toast({
        title: 'Error deleting agent',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleArrayInput = (field: keyof CreateAgentData, value: string) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item);
    setFormData(prev => ({ ...prev, [field]: items }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      role: '',
      description: '',
      system_prompt: '',
      capabilities: [],
      tools: [],
      objectives: [],
      constraints: [],
    });
    setEditingAgent(null);
    setIsFileMode(false);
  };

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      role: agent.role,
      description: agent.description,
      system_prompt: agent.system_prompt,
      capabilities: agent.capabilities || [],
      tools: agent.tools || [],
      objectives: agent.objectives || [],
      constraints: agent.constraints || [],
    });
    setIsFileMode(false);
    onOpen();
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const agentData = JSON.parse(text);
      
      // Validate JSON structure
      if (!agentData.name || !agentData.role || !agentData.description || !agentData.system_prompt) {
        throw new Error('Invalid agent JSON: missing required fields (name, role, description, system_prompt)');
      }

      setFormData({
        name: agentData.name,
        role: agentData.role,
        description: agentData.description,
        system_prompt: agentData.system_prompt,
        capabilities: agentData.capabilities || [],
        tools: agentData.tools || [],
        objectives: agentData.objectives || [],
        constraints: agentData.constraints || [],
      });
      
      toast({
        title: 'Agent loaded from file',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error loading agent file',
        description: error instanceof Error ? error.message : 'Invalid JSON file',
        status: 'error',
        duration: 3000,
      });
    }
  };

  if (loading) {
    return <Text>Loading agents...</Text>;
  }

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading>Agent Management</Heading>
        <HStack spacing={3}>
          <Button leftIcon={<FiPlus />} colorScheme="blue" onClick={() => {
            resetForm();
            onOpen();
          }}>
            Create Agent
          </Button>
        </HStack>
      </Flex>

      {agents.length === 0 ? (
        <Card>
          <CardBody textAlign="center" py={10}>
            <FiUser size={48} style={{ margin: '0 auto 16px' }} />
            <Text fontSize="lg" mb={2}>No agents created yet</Text>
            <Text color="gray.600" mb={4}>Create your first agent to get started with the multi-agent system</Text>
            <Button colorScheme="blue" onClick={onOpen}>Create Your First Agent</Button>
          </CardBody>
        </Card>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          {agents.map(agent => (
            <Card key={agent.id}>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack justify="space-between" width="100%">
                    <Badge colorScheme={agent.status === 'executing' ? 'green' : 'gray'}>
                      {agent.status}
                    </Badge>
                    <HStack spacing={1}>
                      <IconButton
                        aria-label="Edit agent"
                        icon={<FiEdit />}
                        size="sm"
                        variant="ghost"
                        colorScheme="blue"
                        onClick={() => handleEdit(agent)}
                      />
                      <IconButton
                        aria-label="Delete agent"
                        icon={<FiTrash2 />}
                        size="sm"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => handleDelete(agent.id)}
                      />
                    </HStack>
                  </HStack>
                  
                  <Box>
                    <Text fontWeight="bold" fontSize="lg">{agent.name}</Text>
                    <Text color="gray.600" fontSize="sm">{agent.role}</Text>
                  </Box>
                  
                  <Text fontSize="sm" noOfLines={3}>{agent.description}</Text>
                  
                  {agent.capabilities && agent.capabilities.length > 0 && (
                    <Box>
                      <Text fontSize="xs" fontWeight="bold" mb={1}>Capabilities:</Text>
                      <HStack spacing={1} flexWrap="wrap">
                        {agent.capabilities.slice(0, 3).map((cap, idx) => (
                          <Badge key={idx} size="sm" variant="outline">{cap}</Badge>
                        ))}
                        {agent.capabilities.length > 3 && (
                          <Badge size="sm" variant="outline">+{agent.capabilities.length - 3} more</Badge>
                        )}
                      </HStack>
                    </Box>
                  )}
                  
                  <Text fontSize="xs" color="gray.500">
                    Created: {new Date(agent.created_at).toLocaleDateString()}
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <Modal isOpen={isOpen} onClose={() => {
        resetForm();
        onClose();
      }} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{editingAgent ? 'Edit Agent' : 'Create New Agent'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} mb={4}>
              <HStack justify="space-between" width="100%">
                <Text fontSize="sm" color="gray.600">
                  {isFileMode ? 'Load agent configuration from JSON file or fill form manually' : 'Fill the form manually or load from a JSON file'}
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
                  <FormLabel>Upload Agent JSON File</FormLabel>
                  <Input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    size="sm"
                  />
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Select a JSON file containing agent configuration
                  </Text>
                </FormControl>
              )}
            </VStack>
            
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Agent Name</FormLabel>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., research_specialist"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Role</FormLabel>
                  <Input
                    value={formData.role}
                    onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                    placeholder="e.g., Research Specialist"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Brief description of the agent's purpose and expertise"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>System Prompt</FormLabel>
                  <Textarea
                    value={formData.system_prompt}
                    onChange={(e) => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                    placeholder="Detailed instructions for how this agent should behave and respond"
                    rows={4}
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Capabilities</FormLabel>
                  <Input
                    onChange={(e) => handleArrayInput('capabilities', e.target.value)}
                    placeholder="research, analysis, data_collection (comma-separated)"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Tools</FormLabel>
                  <Input
                    onChange={(e) => handleArrayInput('tools', e.target.value)}
                    placeholder="web_search, database_query, document_analysis (comma-separated)"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Objectives</FormLabel>
                  <Input
                    onChange={(e) => handleArrayInput('objectives', e.target.value)}
                    placeholder="gather information, analyze data, provide insights (comma-separated)"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Constraints</FormLabel>
                  <Input
                    onChange={(e) => handleArrayInput('constraints', e.target.value)}
                    placeholder="verify sources, maintain objectivity (comma-separated)"
                  />
                </FormControl>

                <HStack spacing={3} pt={4}>
                  <Button type="submit" colorScheme="blue">
                    {editingAgent ? 'Update Agent' : 'Create Agent'}
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