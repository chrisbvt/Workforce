import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function CrewList() {
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [showResultDialog, setShowResultDialog] = useState(false);
  const [showParamsDialog, setShowParamsDialog] = useState(false);
  const [selectedCrew, setSelectedCrew] = useState(null);
  const [inputParams, setInputParams] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetchCrews();
  }, []);

  const fetchCrews = async () => {
    try {
      const response = await axios.get(`${API_URL}/crews`);
      setCrews(response.data.crews);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch crews');
      setLoading(false);
    }
  };

  const handleExecuteCrew = async (crew) => {
    try {
      // Fetch full crew details first
      const response = await axios.get(`${API_URL}/crews/${crew.id}`);
      const fullCrew = response.data;
      setSelectedCrew(fullCrew);
      
      // Initialize execution parameters
      const initialParams = {
        input_variables: {},  // Crew-level input variables
        task_params: {}       // Task-specific parameters
      };

      // Initialize crew-level input variables
      if (fullCrew.input_variables) {
        Object.keys(fullCrew.input_variables).forEach(key => {
          initialParams.input_variables[key] = '';
        });
      }
      
      // Initialize task parameters
      fullCrew.tasks.forEach(task => {
        initialParams.task_params[task.id] = {
          input_parameters: {},
          context_variables: {}
        };
        if (task.input_parameters) {
          Object.keys(task.input_parameters).forEach(key => {
            initialParams.task_params[task.id].input_parameters[key] = '';
          });
        }
        if (task.context_variables) {
          Object.keys(task.context_variables).forEach(key => {
            initialParams.task_params[task.id].context_variables[key] = '';
          });
        }
      });
      setInputParams(initialParams);
      setShowParamsDialog(true);
    } catch (err) {
      setError('Failed to fetch crew details');
    }
  };

  const handleParameterChange = (type, taskId, paramType, key, value) => {
    setInputParams(prev => {
      if (type === 'crew') {
        return {
          ...prev,
          input_variables: {
            ...prev.input_variables,
            [key]: value
          }
        };
      } else {
        return {
          ...prev,
          task_params: {
            ...prev.task_params,
            [taskId]: {
              ...prev.task_params[taskId],
              [paramType]: {
                ...prev.task_params[taskId][paramType],
                [key]: value
              }
            }
          }
        };
      }
    });
  };

  const handleExecuteWithParams = async () => {
    try {
      if (!selectedCrew) {
        setError('No crew selected');
        return;
      }

      // Get the crew ID from the original crew list
      const crewId = crews.find(c => c.name === selectedCrew.name)?.id;
      if (!crewId) {
        setError('Could not find crew ID');
        return;
      }

      const response = await axios.post(`${API_URL}/crews/${crewId}/execute`, {
        inputs: {
          ...inputParams.input_variables,
          task_params: inputParams.task_params
        }
      });
      setExecutionResult(response.data.result);
      setShowParamsDialog(false);
      setShowResultDialog(true);
    } catch (err) {
      console.error('Error executing crew:', err);
      setError('Failed to execute crew');
      setShowParamsDialog(false);
    }
  };

  const handleDeleteCrew = async (crewId) => {
    try {
      await axios.delete(`${API_URL}/crews/${crewId}`);
      fetchCrews(); // Refresh the list
    } catch (err) {
      setError('Failed to delete crew');
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
        <Typography variant="h4">Crews</Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/create')}
        >
          Create New Crew
        </Button>
      </Box>

      <Grid container spacing={3}>
        {crews.map((crew) => (
          <Grid item xs={12} sm={6} md={4} key={crew.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {crew.name}
                </Typography>
                <Box display="flex" gap={1} mt={2}>
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    onClick={() => navigate(`/crew/${crew.id}`)}
                  >
                    View
                  </Button>
                  <Button
                    variant="contained"
                    color="secondary"
                    size="small"
                    onClick={() => handleExecuteCrew(crew)}
                  >
                    Execute
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => handleDeleteCrew(crew.id)}
                  >
                    Delete
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Parameters Dialog */}
      <Dialog open={showParamsDialog} onClose={() => setShowParamsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Enter Parameters</DialogTitle>
        <DialogContent>
          {/* Crew-level input variables */}
          {selectedCrew && selectedCrew.input_variables && Object.entries(selectedCrew.input_variables).length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Crew Input Variables
              </Typography>
              {Object.entries(selectedCrew.input_variables).map(([varName, varDef]) => (
                <TextField
                  key={varName}
                  fullWidth
                  label={varName}
                  value={inputParams.input_variables?.[varName] || ''}
                  onChange={(e) => handleParameterChange('crew', null, null, varName, e.target.value)}
                  helperText={varDef.description}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          )}

          {/* Task-specific parameters */}
          {selectedCrew && selectedCrew.tasks && selectedCrew.tasks.map((task, index) => (
            <Box key={task.id} sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Task {index + 1}: {task.description.substring(0, 50)}...
              </Typography>
              
              {task.input_parameters && Object.entries(task.input_parameters).length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Input Parameters
                  </Typography>
                  {Object.entries(task.input_parameters).map(([paramName, paramDef]) => (
                    <TextField
                      key={paramName}
                      fullWidth
                      label={paramName}
                      value={inputParams.task_params?.[task.id]?.input_parameters?.[paramName] || ''}
                      onChange={(e) => handleParameterChange('task', task.id, 'input_parameters', paramName, e.target.value)}
                      helperText={paramDef.description}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Box>
              )}

              {task.context_variables && Object.entries(task.context_variables).length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Context Variables
                  </Typography>
                  {Object.entries(task.context_variables).map(([varName, varDef]) => (
                    <TextField
                      key={varName}
                      fullWidth
                      label={varName}
                      value={inputParams.task_params?.[task.id]?.context_variables?.[varName] || ''}
                      onChange={(e) => handleParameterChange('task', task.id, 'context_variables', varName, e.target.value)}
                      helperText={varDef.description}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Box>
              )}
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowParamsDialog(false)}>Cancel</Button>
          <Button onClick={handleExecuteWithParams} variant="contained" color="primary">
            Execute
          </Button>
        </DialogActions>
      </Dialog>

      {/* Results Dialog */}
      <Dialog open={showResultDialog} onClose={() => setShowResultDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Execution Result</DialogTitle>
        <DialogContent>
          <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {executionResult}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResultDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CrewList; 