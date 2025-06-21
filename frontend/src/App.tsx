import { ChakraProvider, Box, Flex, Text, VStack } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import AgentManager from './components/Agents/AgentManager';
import TaskManager from './components/Tasks/TaskManager';
import AdvancedOrchestrator from './components/Orchestration/AdvancedOrchestrator';

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Flex minH="100vh">
          <Sidebar />
          <Box flex="1" p={6} bg="gray.50">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<AgentManager />} />
              <Route path="/tasks" element={<TaskManager />} />
              <Route path="/orchestration" element={<AdvancedOrchestrator />} />
            </Routes>
          </Box>
        </Flex>
      </Router>
    </ChakraProvider>
  );
}

export default App;