import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Input,
  VStack,
  HStack,
  Text,
  Badge,
  List,
  ListItem,
  Alert,
  AlertIcon,
  useToast,
  Divider,
  Spinner,
  Flex,
  Icon,
  Card,
  CardBody,
  useColorModeValue
} from '@chakra-ui/react';
import { FiFolder, FiFile, FiUpload, FiRefreshCw } from 'react-icons/fi';

interface FileInfo {
  name: string;
  size: number;
  modified: number;
  type: 'structured' | 'unstructured' | 'other';
}

interface DirectoryInfo {
  exists: boolean;
  directory: string;
  files: FileInfo[];
  total_files: number;
  error?: string;
}

interface LoadResults {
  agents_loaded: number;
  tasks_loaded: number;
  files_processed: string[];
  errors: string[];
}

const ProjectManager: React.FC = () => {
  const [directory, setDirectory] = useState('/mnt/e/Development/mcp_a2a/project_selfdevelop');
  const [directoryInfo, setDirectoryInfo] = useState<DirectoryInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getApiBase = () => {
    if (typeof window !== 'undefined') {
      const { protocol, hostname } = window.location;
      return `${protocol}//${hostname}:8000`;
    }
    return 'http://localhost:8000';
  };

  const fetchDirectoryInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${getApiBase()}/api/project/directory-info?directory=${encodeURIComponent(directory)}`);
      const data = await response.json();
      setDirectoryInfo(data);
    } catch (error) {
      toast({
        title: 'Error fetching directory info',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000
      });
    } finally {
      setLoading(false);
    }
  };

  const loadFromDirectory = async () => {
    setLoadingFiles(true);
    try {
      const response = await fetch(`${getApiBase()}/api/project/load-from-directory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directory })
      });
      
      if (!response.ok) {
        throw new Error('Failed to load from directory');
      }
      
      const results: LoadResults = await response.json();
      
      toast({
        title: 'Files loaded successfully',
        description: `Loaded ${results.agents_loaded} agents and ${results.tasks_loaded} tasks from ${results.files_processed.length} files`,
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

      // Refresh directory info
      fetchDirectoryInfo();
      
    } catch (error) {
      toast({
        title: 'Error loading files',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000
      });
    } finally {
      setLoadingFiles(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'structured':
        return FiFile;
      case 'unstructured':
        return FiFile;
      default:
        return FiFile;
    }
  };

  const getFileColor = (type: string) => {
    switch (type) {
      case 'structured':
        return 'green';
      case 'unstructured':
        return 'blue';
      default:
        return 'gray';
    }
  };

  useEffect(() => {
    fetchDirectoryInfo();
  }, []);

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Text fontSize="2xl" fontWeight="bold" mb={4}>
            Project File Manager
          </Text>
          <Text color="gray.600" mb={4}>
            Load agents and tasks from project files. Supports JSON (structured) and text/markdown (unstructured) files.
          </Text>
        </Box>

        <Card bg={cardBg} border="1px" borderColor={borderColor}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack>
                <Icon as={FiFolder} />
                <Text fontWeight="medium">Project Directory</Text>
              </HStack>
              
              <HStack>
                <Input
                  value={directory}
                  onChange={(e) => setDirectory(e.target.value)}
                  placeholder="Enter project directory path"
                  flex={1}
                />
                <Button 
                  onClick={fetchDirectoryInfo}
                  leftIcon={<FiRefreshCw />}
                  isLoading={loading}
                  colorScheme="blue"
                  variant="outline"
                >
                  Browse
                </Button>
                <Button
                  onClick={loadFromDirectory}
                  leftIcon={<FiUpload />}
                  isLoading={loadingFiles}
                  colorScheme="green"
                  isDisabled={!directoryInfo?.exists || directoryInfo?.files.length === 0}
                >
                  Load Files
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {loading && (
          <Flex justify="center" align="center" py={8}>
            <Spinner size="lg" />
          </Flex>
        )}

        {directoryInfo && !loading && (
          <Card bg={cardBg} border="1px" borderColor={borderColor}>
            <CardBody>
              {!directoryInfo.exists ? (
                <Alert status="error">
                  <AlertIcon />
                  {directoryInfo.error || 'Directory not found'}
                </Alert>
              ) : (
                <VStack spacing={4} align="stretch">
                  <HStack justify="space-between">
                    <Text fontWeight="medium">
                      Directory: {directoryInfo.directory}
                    </Text>
                    <Badge colorScheme="blue">
                      {directoryInfo.total_files} files
                    </Badge>
                  </HStack>

                  <Divider />

                  {directoryInfo.files.length === 0 ? (
                    <Alert status="info">
                      <AlertIcon />
                      No files found in directory
                    </Alert>
                  ) : (
                    <List spacing={2}>
                      {directoryInfo.files.map((file, index) => (
                        <ListItem key={index}>
                          <Card variant="outline" size="sm">
                            <CardBody py={3}>
                              <HStack justify="space-between">
                                <HStack>
                                  <Icon as={getFileIcon(file.type)} />
                                  <Text fontWeight="medium">{file.name}</Text>
                                  <Badge 
                                    colorScheme={getFileColor(file.type)}
                                    size="sm"
                                  >
                                    {file.type}
                                  </Badge>
                                </HStack>
                                <HStack spacing={4} fontSize="sm" color="gray.600">
                                  <Text>{formatFileSize(file.size)}</Text>
                                  <Text>{formatDate(file.modified)}</Text>
                                </HStack>
                              </HStack>
                            </CardBody>
                          </Card>
                        </ListItem>
                      ))}
                    </List>
                  )}
                </VStack>
              )}
            </CardBody>
          </Card>
        )}

        <Card bg={cardBg} border="1px" borderColor={borderColor}>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <Text fontWeight="medium">File Format Guide</Text>
              <VStack spacing={2} align="stretch" fontSize="sm">
                <HStack>
                  <Badge colorScheme="green">JSON (Structured)</Badge>
                  <Text>{"{ \"agents\": [...], \"tasks\": [...] }"}</Text>
                </HStack>
                <HStack>
                  <Badge colorScheme="blue">Text/MD (Unstructured)</Badge>
                  <Text>Natural language descriptions parsed automatically</Text>
                </HStack>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
};

export default ProjectManager;