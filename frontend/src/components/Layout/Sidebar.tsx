import { Box, VStack, Text, Icon, Link, Heading } from '@chakra-ui/react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { FiHome, FiUsers, FiCheckSquare, FiGitBranch } from 'react-icons/fi';

const navItems = [
  { name: 'Dashboard', path: '/', icon: FiHome },
  { name: 'Agents', path: '/agents', icon: FiUsers },
  { name: 'Tasks', path: '/tasks', icon: FiCheckSquare },
  { name: 'Orchestration', path: '/orchestration', icon: FiGitBranch },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <Box
      w="250px"
      bg="white"
      borderRight="1px"
      borderColor="gray.200"
      p={4}
      shadow="sm"
    >
      <Heading size="md" mb={8} color="blue.600">
        🤖 MCP Multi-Agent System
      </Heading>
      
      <VStack spacing={2} align="stretch">
        {navItems.map((item) => (
          <Link
            as={RouterLink}
            to={item.path}
            key={item.path}
            p={3}
            borderRadius="md"
            display="flex"
            alignItems="center"
            bg={location.pathname === item.path ? 'blue.50' : 'transparent'}
            color={location.pathname === item.path ? 'blue.600' : 'gray.600'}
            _hover={{
              bg: location.pathname === item.path ? 'blue.50' : 'gray.50',
              textDecoration: 'none',
            }}
          >
            <Icon as={item.icon} mr={3} />
            <Text>{item.name}</Text>
          </Link>
        ))}
      </VStack>
    </Box>
  );
}