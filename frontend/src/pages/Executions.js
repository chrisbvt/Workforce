import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function Executions() {
  const [executions, setExecutions] = useState([]);
  const [crews, setCrews] = useState([]);
  const [selectedCrew, setSelectedCrew] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const navigate = useNavigate();
  const { crewId } = useParams();

  useEffect(() => {
    fetchCrews();
    if (crewId) {
      setSelectedCrew(crewId);
      fetchCrewExecutions(crewId);
    } else {
      fetchExecutions();
    }
  }, [crewId]);

  const fetchCrews = async () => {
    try {
      const response = await axios.get(`${API_URL}/crews`);
      setCrews(response.data.crews || []);
    } catch (err) {
      console.error('Error fetching crews:', err);
    }
  };

  const fetchExecutions = async () => {
    try {
      const response = await axios.get(`${API_URL}/crews/executions`);
      setExecutions(response.data.executions || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching executions:', err);
      handleError(err);
    }
  };

  const fetchCrewExecutions = async (crewId) => {
    try {
      const response = await axios.get(`${API_URL}/crews/${crewId}/executions`);
      setExecutions(response.data.executions || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching crew executions:', err);
      handleError(err);
    }
  };

  const handleError = (err) => {
    if (err.response?.status === 404) {
      setExecutions([]);
      setLoading(false);
      return;
    }
    
    let errorMessage = 'Failed to fetch executions';
    
    if (err.response?.data) {
      if (typeof err.response.data === 'string') {
        errorMessage = err.response.data;
      } else if (Array.isArray(err.response.data)) {
        errorMessage = err.response.data.map(e => {
          const location = e.loc ? e.loc.join('.') : '';
          return `${location}: ${e.msg}`;
        }).join('\n');
      } else if (err.response.data.detail) {
        errorMessage = typeof err.response.data.detail === 'object' 
          ? JSON.stringify(err.response.data.detail)
          : err.response.data.detail.toString();
      } else if (typeof err.response.data === 'object') {
        errorMessage = Object.values(err.response.data)
          .map(e => typeof e === 'string' ? e : (e.msg || JSON.stringify(e)))
          .join(', ');
      }
    }
    
    setError(errorMessage);
    setLoading(false);
  };

  const handleCrewChange = (event) => {
    const crewId = event.target.value;
    setSelectedCrew(crewId);
    if (crewId) {
      fetchCrewExecutions(crewId);
    } else {
      fetchExecutions();
    }
  };

  const handleViewDetails = (execution) => {
    setSelectedExecution(execution);
    setShowDetailsDialog(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          {selectedCrew ? 'Crew Executions' : 'All Executions'}
        </Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Crew Filter</InputLabel>
          <Select
            value={selectedCrew}
            label="Crew Filter"
            onChange={handleCrewChange}
          >
            <MenuItem value="">All Executions</MenuItem>
            {crews.map((crew) => (
              <MenuItem key={crew.id} value={crew.id}>
                {crew.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {executions.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No executions found. Execute a crew to see results here.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Crew Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Started At</TableCell>
                <TableCell>Completed At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {executions.map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell>{execution.crew_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={execution.status}
                      color={getStatusColor(execution.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(execution.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    {execution.completed_at
                      ? new Date(execution.completed_at).toLocaleString()
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => handleViewDetails(execution)}
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Execution Details</DialogTitle>
        <DialogContent>
          {selectedExecution && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Crew: {selectedExecution.crew_name}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                Status: {selectedExecution.status}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                Started: {new Date(selectedExecution.created_at).toLocaleString()}
              </Typography>
              {selectedExecution.completed_at && (
                <Typography variant="subtitle1" gutterBottom>
                  Completed: {new Date(selectedExecution.completed_at).toLocaleString()}
                </Typography>
              )}
              {selectedExecution.allowed_tools && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Allowed Tools
                  </Typography>
                  <Paper sx={{ p: 2 }}>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {selectedExecution.allowed_tools.map((tool, index) => (
                        <Chip
                          key={index}
                          label={tool}
                          color="primary"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Paper>
                </Box>
              )}
              <Typography variant="subtitle1" gutterBottom>
                Input Variables:
              </Typography>
              <Paper sx={{ p: 2, mb: 2 }}>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(selectedExecution.input_variables, null, 2)}
                </pre>
              </Paper>
              <Typography variant="subtitle1" gutterBottom>
                Task Parameters:
              </Typography>
              <Paper sx={{ p: 2, mb: 2 }}>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(selectedExecution.task_params, null, 2)}
                </pre>
              </Paper>
              {selectedExecution.result && (
                <>
                  <Typography variant="subtitle1" gutterBottom>
                    Result:
                  </Typography>
                  <Paper sx={{ p: 2 }}>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {selectedExecution.result}
                    </pre>
                  </Paper>
                </>
              )}
              {selectedExecution.error && (
                <>
                  <Typography variant="subtitle1" gutterBottom color="error">
                    Error:
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'error.light' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {selectedExecution.error}
                    </pre>
                  </Paper>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Executions; 