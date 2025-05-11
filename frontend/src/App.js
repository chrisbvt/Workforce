import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Link as RouterLink } from 'react-router-dom';

// Pages
import CrewList from './pages/CrewList';
import CrewCreate from './pages/CrewCreate';
import CrewDetail from './pages/CrewDetail';
import CrewEdit from './pages/CrewEdit';
import CrewExecutions from './pages/CrewExecutions';
import Executions from './pages/Executions';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Agent Workforce
              </Typography>
              <Button color="inherit" component={RouterLink} to="/">
                Crews
              </Button>
              <Button color="inherit" component={RouterLink} to="/executions">
                Executions
              </Button>
              <Button color="inherit" component={RouterLink} to="/create">
                Create Crew
              </Button>
            </Toolbar>
          </AppBar>
          <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Routes>
              <Route path="/" element={<CrewList />} />
              <Route path="/create" element={<CrewCreate />} />
              <Route path="/crew/:id" element={<CrewDetail />} />
              <Route path="/crew/:id/edit" element={<CrewEdit />} />
              <Route path="/crew/:id/executions" element={<CrewExecutions />} />
              <Route path="/executions" element={<Executions />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 