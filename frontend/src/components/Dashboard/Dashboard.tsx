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
  Text,
  Badge,
  VStack,
  HStack,
} from '@chakra-ui/react';
import { apiService, Agent, Task } from '../../services/api';

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Dashboard: Fetching data...');
        const [agentsData, tasksData] = await Promise.all([
          apiService.getAgents(),
          apiService.getTasks(),
        ]);
        console.log('Dashboard: Data fetched successfully', { agents: agentsData.length, tasks: tasksData.length });
        setAgents(agentsData);
        setTasks(tasksData);
      } catch (error) {
        console.error('Dashboard: Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

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
                  <Badge colorScheme={agent.status === 'executing' ? 'green' : 'gray'}>
                    {agent.status}
                  </Badge>
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
    </Box>
  );
}