import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditIcon from '@mui/icons-material/Edit';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function CrewDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [crew, setCrew] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [showResultDialog, setShowResultDialog] = useState(false);
  const [showParamsDialog, setShowParamsDialog] = useState(false);
  const [inputParams, setInputParams] = useState({});

  useEffect(() => {
    fetchCrew();
  }, [id]);

  const fetchCrew = async () => {
    try {
      const response = await axios.get(`${API_URL}/crews/${id}`);
      setCrew(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch crew details');
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    try {
      // Initialize execution parameters
      const initialParams = {
        input_variables: {},  // Crew-level input variables
        task_params: {}       // Task-specific parameters
      };

      // Initialize crew-level input variables
      if (crew.input_variables) {
        Object.keys(crew.input_variables).forEach(key => {
          initialParams.input_variables[key] = '';
        });
      }
      
      // Initialize task parameters
      crew.tasks.forEach(task => {
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
      setError('Failed to prepare execution parameters');
    }
  };

  const handleParamsChange = (type, taskId, paramType, key, value) => {
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
      const response = await axios.post(`${API_URL}/crews/${crew.id}/execute`, {
        inputs: {
          ...inputParams.input_variables,
          ...Object.entries(inputParams.task_params).reduce((acc, [taskId, params]) => ({
            ...acc,
            ...params.input_parameters
          }), {})
        }
      });
      setExecutionResult(response.data.result);
      setShowParamsDialog(false);
      setShowResultDialog(true);
    } catch (err) {
      setError('Failed to execute crew');
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API_URL}/crews/${id}`);
      navigate('/');
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

  if (!crew) {
    return <Alert severity="error">Crew not found</Alert>;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          {crew.name}
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/crew/${id}/edit`)}
          >
            Edit
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => navigate(`/crew/${id}/executions`)}
          >
            View Executions
          </Button>
          <Button
            variant="outlined"
            color="error"
            onClick={handleDelete}
          >
            Delete
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Description
        </Typography>
        <Typography>{crew.description}</Typography>
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Agents
            </Typography>
            {crew.agents.map((agent, index) => (
              <Paper key={index} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  {agent.role}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Goal: {agent.goal}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Backstory: {agent.backstory}
                </Typography>
                <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                  LLM Configuration
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Provider: {agent.llm_config.provider}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Model: {agent.llm_config.model}
                </Typography>
                {agent.llm_config.provider === 'openai_compatible' && agent.llm_config.base_url && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Base URL: {agent.llm_config.base_url}
                  </Typography>
                )}
                {agent.llm_config.provider !== 'anthropic' && agent.llm_config.api_version && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    API Version: {agent.llm_config.api_version}
                  </Typography>
                )}
                {agent.allowed_tools && agent.allowed_tools.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                      Allowed Tools
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {agent.allowed_tools.map((tool, index) => (
                        <Chip
                          key={index}
                          label={tool}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </>
                )}
              </Paper>
            ))}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Tasks
            </Typography>
            {crew.tasks.map((task, index) => (
              <Paper key={index} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Task {index + 1}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Description: {task.description}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Agent: {task.agent}
                </Typography>
                {task.expected_output && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Expected Output: {task.expected_output}
                  </Typography>
                )}
                {task.input_parameters && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                      Input Parameters
                    </Typography>
                    <Typography variant="body2" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(task.input_parameters, null, 2)}
                    </Typography>
                  </>
                )}
                {task.context_variables && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                      Context Variables
                    </Typography>
                    <Typography variant="body2" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(task.context_variables, null, 2)}
                    </Typography>
                  </>
                )}
                {task.dependencies && task.dependencies.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                      Dependencies
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Depends on tasks: {task.dependencies.join(', ')}
                    </Typography>
                  </>
                )}
              </Paper>
            ))}
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={showParamsDialog} onClose={() => setShowParamsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Enter Parameters</DialogTitle>
        <DialogContent>
          {/* Crew-level input variables */}
          {crew.input_variables && Object.entries(crew.input_variables).length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Crew Input Variables
              </Typography>
              {Object.entries(crew.input_variables).map(([varName, varDef]) => (
                <TextField
                  key={varName}
                  fullWidth
                  label={varName}
                  value={inputParams.input_variables?.[varName] || ''}
                  onChange={(e) => handleParamsChange('crew', null, null, varName, e.target.value)}
                  helperText={varDef.description}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          )}

          {/* Task-specific parameters */}
          {crew.tasks.map((task, index) => (
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
                      onChange={(e) => handleParamsChange('task', task.id, 'input_parameters', paramName, e.target.value)}
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
                      onChange={(e) => handleParamsChange('task', task.id, 'context_variables', varName, e.target.value)}
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

export default CrewDetail; 