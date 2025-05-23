import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Grid,
  IconButton,
  Alert,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  OutlinedInput,
  InputAdornment,
  Chip,
  Select,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import KeyIcon from '@mui/icons-material/Key';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import axios from 'axios';
import { LLM_MODELS, DEFAULT_LLM_CONFIG } from '../config/llmConfig';

const API_URL = 'http://localhost:8000/api';

function CrewCreate() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [crew, setCrew] = useState({
    name: '',
    description: '',
    input_variables: {},
    output_variables: {},
    agents: [
      {
        role: '',
        goal: '',
        backstory: '',
        verbose: true,
        llm_provider: "anthropic",
        llm_model: "claude-3-5-haiku-20241022",
        llm_base_url: null,
        llm_api_key: null,
        llm_api_version: null
      },
    ],
    tasks: [
      {
        description: '',
        agent_role: '',
        expected_output: '',
        input_parameters: {},
        context_variables: {},
        output_variables: {},
        dependencies: []
      },
    ],
  });

  const handleAgentChange = (index, field, value) => {
    const newAgents = [...crew.agents];
    newAgents[index][field] = value;
    setCrew({ ...crew, agents: newAgents });
  };

  const handleTaskChange = (index, field, value) => {
    const newTasks = [...crew.tasks];
    if (field === 'input_parameters' || field === 'context_variables') {
      try {
        // Try to parse if it's a JSON string
        newTasks[index][field] = typeof value === 'string' ? JSON.parse(value) : value;
      } catch (e) {
        // If parsing fails, store as is
        newTasks[index][field] = value;
      }
    } else if (field === 'dependencies') {
      try {
        // Try to parse if it's a JSON string
        newTasks[index][field] = typeof value === 'string' ? JSON.parse(value) : value;
      } catch (e) {
        // If parsing fails, store as empty array
        newTasks[index][field] = [];
      }
    } else if (field === 'description') {
      // Only process parameters if the last character is a closing brace
      if (value.endsWith('}')) {
        // Extract parameters from description
        const paramMatches = value.match(/\{([^}]+)\}/g) || [];
        const params = paramMatches.map(match => match.slice(1, -1)); // Remove curly braces
        
        // Get existing parameters
        const existingParams = { ...(newTasks[index].input_parameters || {}) };
        
        // Add new parameters that don't exist yet
        params.forEach(param => {
          if (!existingParams[param]) {
            existingParams[param] = `Parameter for ${param}`;
          }
        });
        
        // Remove parameters that are no longer in the description
        Object.keys(existingParams).forEach(param => {
          if (!params.includes(param)) {
            delete existingParams[param];
          }
        });
        
        newTasks[index].input_parameters = existingParams;
      }
      newTasks[index][field] = value;
    } else {
      newTasks[index][field] = value;
    }
    setCrew({ ...crew, tasks: newTasks });
  };

  const handleParameterChange = (taskIndex, type, key, value) => {
    const newTasks = [...crew.tasks];
    const currentParams = newTasks[taskIndex][type] || {};
    newTasks[taskIndex][type] = {
      ...currentParams,
      [key]: value
    };
    setCrew({ ...crew, tasks: newTasks });
  };

  const removeParameter = (taskIndex, type, key) => {
    const newTasks = [...crew.tasks];
    const currentParams = { ...newTasks[taskIndex][type] };
    delete currentParams[key];
    newTasks[taskIndex][type] = currentParams;
    setCrew({ ...crew, tasks: newTasks });
  };

  const addParameter = (taskIndex, type) => {
    const newTasks = [...crew.tasks];
    const currentParams = newTasks[taskIndex][type] || {};
    newTasks[taskIndex][type] = {
      ...currentParams,
      "": ""
    };
    setCrew({ ...crew, tasks: newTasks });
  };

  const addAgent = () => {
    setCrew({
      ...crew,
      agents: [
        ...crew.agents,
        {
          role: '',
          goal: '',
          backstory: '',
          verbose: true,
          llm_provider: "anthropic",
          llm_model: "claude-3-5-haiku-20241022",
          llm_base_url: null,
          llm_api_key: null,
          llm_api_version: null
        },
      ],
    });
  };

  const addTask = () => {
    setCrew({
      ...crew,
      tasks: [
        ...crew.tasks,
        {
          description: '',
          agent_role: '',
          expected_output: '',
          input_parameters: {},
          context_variables: {},
          output_variables: {},
          dependencies: []
        },
      ],
    });
  };

  const removeAgent = (index) => {
    const newAgents = crew.agents.filter((_, i) => i !== index);
    setCrew({ ...crew, agents: newAgents });
  };

  const removeTask = (index) => {
    const newTasks = crew.tasks.filter((_, i) => i !== index);
    setCrew({ ...crew, tasks: newTasks });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    let transformedCrew;
    try {
      // Transform the data to match the backend's expected format
      transformedCrew = {
        ...crew,
        agents: crew.agents.map(agent => ({
          role: agent.role,
          goal: agent.goal,
          backstory: agent.backstory,
          verbose: agent.verbose,
          allowed_tools: agent.allowed_tools || [],
          llm_config: {
            provider: agent.llm_provider,
            model: agent.llm_model,
            base_url: agent.llm_base_url,
            api_key: agent.llm_api_key,
            api_version: agent.llm_api_version
          }
        })),
        tasks: crew.tasks.map(task => ({
          ...task,
          input_parameters: Object.entries(task.input_parameters || {}).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              name: key,
              description: value,
              type: "string",
              required: true
            }
          }), {}),
          context_variables: Object.entries(task.context_variables || {}).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              name: key,
              description: value,
              type: "string",
              required: true
            }
          }), {}),
          output_variables: Object.entries(task.output_variables || {}).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              name: key,
              description: value,
              type: "string",
              required: true
            }
          }), {})
        })),
        // Transform crew-level variables
        input_variables: Object.entries(crew.input_variables || {}).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: {
            name: key,
            description: value,
            type: "string",
            required: true
          }
        }), {}),
        output_variables: Object.entries(crew.output_variables || {}).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: {
            name: key,
            description: value,
            type: "string",
            required: true
          }
        }), {})
      };

      console.log('Sending crew data:', JSON.stringify(transformedCrew, null, 2));
      const response = await axios.post(`${API_URL}/crews`, transformedCrew);
      console.log('Response:', response.data);
      navigate('/');
    } catch (err) {
      console.error('Error creating crew:', err.response?.data || err);
      console.error('Request payload:', JSON.stringify(crew, null, 2));
      console.error('Transformed payload:', JSON.stringify(transformedCrew, null, 2));
      // Handle validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Handle array of validation errors
          const errorMessages = err.response.data.detail.map(e => {
            console.error('Validation error:', e);
            return `${e.loc.join('.')}: ${e.msg}`;
          }).join(', ');
          setError(errorMessages);
        } else {
          // Handle single error message
          setError(err.response.data.detail);
        }
      } else {
        setError('Failed to create crew');
      }
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Typography variant="h4" gutterBottom>
        Create New Crew
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Crew Details
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Crew Name"
              value={crew.name}
              onChange={(e) => setCrew({ ...crew, name: e.target.value })}
              required
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={crew.description}
              onChange={(e) => setCrew({ ...crew, description: e.target.value })}
              multiline
              rows={2}
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Crew Variables</Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Input Variables</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Define variables that will be available to all tasks in the crew. Use {'{crew_variable_name}'} in your task descriptions to reference these variables.
                </Typography>
                <Box mb={2}>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => {
                      const newVars = { ...crew.input_variables, "": "" };
                      setCrew({ ...crew, input_variables: newVars });
                    }}
                    size="small"
                  >
                    Add Input Variable
                  </Button>
                </Box>
                {Object.entries(crew.input_variables).map(([key, value], index) => (
                  <Grid container spacing={2} key={index} alignItems="center" sx={{ mb: 1 }}>
                    <Grid item xs={5}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Variable Name</InputLabel>
                        <OutlinedInput
                          value={key}
                          onChange={(e) => {
                            const newKey = e.target.value;
                            const currentValue = crew.input_variables[key];
                            const newVars = { ...crew.input_variables };
                            delete newVars[key];
                            newVars[newKey] = currentValue;
                            setCrew({ ...crew, input_variables: newVars });
                          }}
                          startAdornment={
                            <InputAdornment position="start">
                              <KeyIcon />
                            </InputAdornment>
                          }
                          helperText="Name of the variable (use in tasks as {'{crew_name}'})"
                        />
                      </FormControl>
                    </Grid>
                    <Grid item xs={5}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Description</InputLabel>
                        <OutlinedInput
                          value={value}
                          onChange={(e) => {
                            const newVars = { ...crew.input_variables };
                            newVars[key] = e.target.value;
                            setCrew({ ...crew, input_variables: newVars });
                          }}
                          startAdornment={
                            <InputAdornment position="start">
                              <TextFieldsIcon />
                            </InputAdornment>
                          }
                          helperText="Description of what this variable is for"
                        />
                      </FormControl>
                    </Grid>
                    <Grid item xs={2}>
                      <IconButton
                        onClick={() => {
                          const newVars = { ...crew.input_variables };
                          delete newVars[key];
                          setCrew({ ...crew, input_variables: newVars });
                        }}
                        color="error"
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                ))}
              </AccordionDetails>
            </Accordion>
          </Grid>
          <Grid item xs={12} md={6}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Output Variables</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Define variables that will be produced by the crew. These can be used to track the overall output of the crew.
                </Typography>
                <Box mb={2}>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => {
                      const newVars = { ...crew.output_variables, "": "" };
                      setCrew({ ...crew, output_variables: newVars });
                    }}
                    size="small"
                  >
                    Add Output Variable
                  </Button>
                </Box>
                {Object.entries(crew.output_variables).map(([key, value], index) => (
                  <Grid container spacing={2} key={index} alignItems="center" sx={{ mb: 1 }}>
                    <Grid item xs={5}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Variable Name</InputLabel>
                        <OutlinedInput
                          value={key}
                          onChange={(e) => {
                            const newKey = e.target.value;
                            const currentValue = crew.output_variables[key];
                            const newVars = { ...crew.output_variables };
                            delete newVars[key];
                            newVars[newKey] = currentValue;
                            setCrew({ ...crew, output_variables: newVars });
                          }}
                          startAdornment={
                            <InputAdornment position="start">
                              <KeyIcon />
                            </InputAdornment>
                          }
                          helperText="Name of the output variable"
                        />
                      </FormControl>
                    </Grid>
                    <Grid item xs={5}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Description</InputLabel>
                        <OutlinedInput
                          value={value}
                          onChange={(e) => {
                            const newVars = { ...crew.output_variables };
                            newVars[key] = e.target.value;
                            setCrew({ ...crew, output_variables: newVars });
                          }}
                          startAdornment={
                            <InputAdornment position="start">
                              <TextFieldsIcon />
                            </InputAdornment>
                          }
                          helperText="Description of what this output represents"
                        />
                      </FormControl>
                    </Grid>
                    <Grid item xs={2}>
                      <IconButton
                        onClick={() => {
                          const newVars = { ...crew.output_variables };
                          delete newVars[key];
                          setCrew({ ...crew, output_variables: newVars });
                        }}
                        color="error"
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                ))}
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Agents
        </Typography>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Button startIcon={<AddIcon />} onClick={addAgent}>
            Add Agent
          </Button>
        </Box>
        {crew.agents.map((agent, index) => (
          <Paper key={index} sx={{ p: 2, mb: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">Agent {index + 1}</Typography>
              <IconButton onClick={() => removeAgent(index)} color="error">
                <DeleteIcon />
              </IconButton>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Role"
                  value={agent.role}
                  onChange={(e) => handleAgentChange(index, 'role', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Goal"
                  value={agent.goal}
                  onChange={(e) => handleAgentChange(index, 'goal', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Backstory"
                  value={agent.backstory}
                  onChange={(e) => handleAgentChange(index, 'backstory', e.target.value)}
                  multiline
                  rows={2}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  LLM Configuration
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      select
                      fullWidth
                      label="Provider"
                      value={agent.llm_provider}
                      onChange={(e) => handleAgentChange(index, 'llm_provider', e.target.value)}
                    >
                      <MenuItem value="anthropic">Anthropic</MenuItem>
                      <MenuItem value="openai">OpenAI</MenuItem>
                      <MenuItem value="openai_compatible">OpenAI Compatible</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      select
                      fullWidth
                      label="Model"
                      value={agent.llm_model}
                      onChange={(e) => handleAgentChange(index, 'llm_model', e.target.value)}
                      helperText={
                        agent.llm_provider === 'anthropic' 
                          ? 'Select a Claude model'
                          : agent.llm_provider === 'openai'
                          ? 'Select an OpenAI model'
                          : 'Select a model for your OpenAI-compatible endpoint'
                      }
                    >
                      {LLM_MODELS[agent.llm_provider].map((model) => (
                        <MenuItem key={model.value} value={model.value}>
                          {model.label}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                  {agent.llm_provider === 'openai_compatible' && (
                    <>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Base URL"
                          value={agent.llm_base_url || ''}
                          onChange={(e) => handleAgentChange(index, 'llm_base_url', e.target.value)}
                          helperText="URL for your OpenAI-compatible API endpoint"
                        />
                      </Grid>
                      {agent.llm_model === 'custom' && (
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Custom Model Name"
                            value={agent.llm_model}
                            onChange={(e) => handleAgentChange(index, 'llm_model', e.target.value)}
                            helperText="Enter your custom model name"
                          />
                        </Grid>
                      )}
                    </>
                  )}
                  {agent.llm_provider !== 'anthropic' && (
                    <>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="API Key"
                          type="password"
                          value={agent.llm_api_key || ''}
                          onChange={(e) => handleAgentChange(index, 'llm_api_key', e.target.value)}
                          helperText={
                            agent.llm_provider === 'openai'
                              ? 'Your OpenAI API key'
                              : 'API key for your OpenAI-compatible endpoint'
                          }
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="API Version"
                          value={agent.llm_api_version || ''}
                          onChange={(e) => handleAgentChange(index, 'llm_api_version', e.target.value)}
                          helperText="Optional: API version (e.g., 2024-02-15)"
                        />
                      </Grid>
                    </>
                  )}
                </Grid>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Allowed Tools
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Tools</InputLabel>
                  <Select
                    multiple
                    value={agent.allowed_tools || []}
                    onChange={(e) => handleAgentChange(index, 'allowed_tools', e.target.value)}
                    input={<OutlinedInput label="Select Tools" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    <MenuItem value="SearchTool">Search Tool</MenuItem>
                    <MenuItem value="WebScrapingTool">Web Scraping Tool</MenuItem>
                    <MenuItem value="DataAnalysisTool">Data Analysis Tool</MenuItem>
                    <MenuItem value="FileOperationTool">File Operation Tool</MenuItem>
                    <MenuItem value="JiraTool">Jira Tool</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        ))}
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Tasks</Typography>
          <Button startIcon={<AddIcon />} onClick={addTask}>
            Add Task
          </Button>
        </Box>
        {crew.tasks.map((task, index) => (
          <Paper key={index} sx={{ p: 2, mb: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">Task {index + 1}</Typography>
              <IconButton onClick={() => removeTask(index)} color="error">
                <DeleteIcon />
              </IconButton>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={task.description}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Check if user just typed an opening brace
                    if (value.endsWith('{') && !value.endsWith('{}')) {
                      // Add closing brace
                      handleTaskChange(index, 'description', value + '}');
                    } else {
                      handleTaskChange(index, 'description', value);
                    }
                  }}
                  required
                  multiline
                  rows={3}
                  helperText="Use {parameter_name} to reference input parameters in your description"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  select
                  fullWidth
                  label="Agent Role"
                  value={task.agent_role}
                  onChange={(e) => handleTaskChange(index, 'agent_role', e.target.value)}
                  required
                  helperText="Select the agent that will perform this task"
                >
                  {crew.agents.filter(agent => agent.role).map((agent) => (
                    <MenuItem key={agent.role} value={agent.role}>
                      {agent.role}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Expected Output"
                  value={task.expected_output}
                  onChange={(e) => handleTaskChange(index, 'expected_output', e.target.value)}
                  multiline
                  rows={2}
                  helperText="Describe what the task should produce"
                />
              </Grid>

              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Input Parameters</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Define the parameters that will be required when executing this task. Use {'{parameter_name}'} in your task description to reference these parameters.
                    </Typography>
                    <Box mb={2}>
                      <Button
                        startIcon={<AddIcon />}
                        onClick={() => addParameter(index, 'input_parameters')}
                        size="small"
                      >
                        Add Parameter Definition
                      </Button>
                    </Box>
                    {Object.entries(task.input_parameters || {}).map(([key, value], paramIndex) => (
                      <Grid container spacing={2} key={paramIndex} alignItems="center" sx={{ mb: 1 }}>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Parameter Name</InputLabel>
                            <OutlinedInput
                              value={key}
                              onChange={(e) => {
                                const newKey = e.target.value;
                                const currentValue = task.input_parameters[key];
                                removeParameter(index, 'input_parameters', key);
                                handleParameterChange(index, 'input_parameters', newKey, currentValue);
                                // Update description to use new parameter name
                                const newDescription = task.description.replace(
                                  `{${key}}`,
                                  `{${newKey}}`
                                );
                                handleTaskChange(index, 'description', newDescription);
                              }}
                              startAdornment={
                                <InputAdornment position="start">
                                  <KeyIcon />
                                </InputAdornment>
                              }
                              helperText="Name of the parameter (use in description as {'{name}'})"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Description</InputLabel>
                            <OutlinedInput
                              value={value}
                              onChange={(e) => handleParameterChange(index, 'input_parameters', key, e.target.value)}
                              startAdornment={
                                <InputAdornment position="start">
                                  <TextFieldsIcon />
                                </InputAdornment>
                              }
                              helperText="Description of what this parameter is for"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            onClick={() => {
                              removeParameter(index, 'input_parameters', key);
                              // Remove parameter from description
                              const newDescription = task.description.replace(
                                `{${key}}`,
                                ''
                              );
                              handleTaskChange(index, 'description', newDescription);
                            }}
                            color="error"
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    ))}
                  </AccordionDetails>
                </Accordion>
              </Grid>

              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Context Variables</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Define variables that will be available during task execution. Use {'{variable_name}'} in your task description to reference these variables.
                    </Typography>
                    <Box mb={2}>
                      <Button
                        startIcon={<AddIcon />}
                        onClick={() => addParameter(index, 'context_variables')}
                        size="small"
                      >
                        Add Variable
                      </Button>
                    </Box>
                    {Object.entries(task.context_variables || {}).map(([key, value], varIndex) => (
                      <Grid container spacing={2} key={varIndex} alignItems="center" sx={{ mb: 1 }}>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Variable Name</InputLabel>
                            <OutlinedInput
                              value={key}
                              onChange={(e) => {
                                const newKey = e.target.value;
                                const currentValue = task.context_variables[key];
                                removeParameter(index, 'context_variables', key);
                                handleParameterChange(index, 'context_variables', newKey, currentValue);
                                // Update description to use new variable name
                                const newDescription = task.description.replace(
                                  `{${key}}`,
                                  `{${newKey}}`
                                );
                                handleTaskChange(index, 'description', newDescription);
                              }}
                              startAdornment={
                                <InputAdornment position="start">
                                  <KeyIcon />
                                </InputAdornment>
                              }
                              helperText="Name of the variable (use in description as {'{name}'})"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Value</InputLabel>
                            <OutlinedInput
                              value={value}
                              onChange={(e) => handleParameterChange(index, 'context_variables', key, e.target.value)}
                              startAdornment={
                                <InputAdornment position="start">
                                  <TextFieldsIcon />
                                </InputAdornment>
                              }
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            onClick={() => {
                              removeParameter(index, 'context_variables', key);
                              // Remove variable from description
                              const newDescription = task.description.replace(
                                `{${key}}`,
                                ''
                              );
                              handleTaskChange(index, 'description', newDescription);
                            }}
                            color="error"
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    ))}
                  </AccordionDetails>
                </Accordion>
              </Grid>

              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Dependencies</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Define tasks that this task depends on. Use {'{task_id}'} in dependent tasks to reference this task.
                    </Typography>
                    <Box mb={2}>
                      <Button
                        startIcon={<AddIcon />}
                        onClick={() => {
                          const newDeps = [...task.dependencies, ""]
                          handleTaskChange(index, 'dependencies', JSON.stringify(newDeps));
                        }}
                        size="small"
                      >
                        Add Dependency
                      </Button>
                    </Box>
                    {task.dependencies.map((dep, depIndex) => (
                      <Grid container spacing={2} key={depIndex} alignItems="center" sx={{ mb: 1 }}>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Task ID</InputLabel>
                            <OutlinedInput
                              value={dep}
                              onChange={(e) => {
                                const newDeps = [...task.dependencies];
                                newDeps[depIndex] = e.target.value;
                                handleTaskChange(index, 'dependencies', JSON.stringify(newDeps));
                              }}
                              startAdornment={
                                <InputAdornment position="start">
                                  <KeyIcon />
                                </InputAdornment>
                              }
                              helperText="ID of the task to depend on"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Description</InputLabel>
                            <OutlinedInput
                              value={dep}
                              onChange={(e) => {
                                const newDeps = [...task.dependencies];
                                newDeps[depIndex] = e.target.value;
                                handleTaskChange(index, 'dependencies', JSON.stringify(newDeps));
                              }}
                              startAdornment={
                                <InputAdornment position="start">
                                  <TextFieldsIcon />
                                </InputAdornment>
                              }
                              helperText="Description of the dependency"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            onClick={() => {
                              const newDeps = [...task.dependencies];
                              newDeps.splice(depIndex, 1);
                              handleTaskChange(index, 'dependencies', JSON.stringify(newDeps));
                            }}
                            color="error"
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    ))}
                  </AccordionDetails>
                </Accordion>
              </Grid>

              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Output Variables</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Define variables that this task will produce. These can be used by dependent tasks. Use {'{task_id_variable_name}'} in dependent tasks to reference these variables.
                    </Typography>
                    <Box mb={2}>
                      <Button
                        startIcon={<AddIcon />}
                        onClick={() => addParameter(index, 'output_variables')}
                        size="small"
                      >
                        Add Output Variable
                      </Button>
                    </Box>
                    {Object.entries(task.output_variables || {}).map(([key, value], varIndex) => (
                      <Grid container spacing={2} key={varIndex} alignItems="center" sx={{ mb: 1 }}>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Variable Name</InputLabel>
                            <OutlinedInput
                              value={key}
                              onChange={(e) => {
                                const newKey = e.target.value;
                                const currentValue = task.output_variables[key];
                                removeParameter(index, 'output_variables', key);
                                handleParameterChange(index, 'output_variables', newKey, currentValue);
                              }}
                              startAdornment={
                                <InputAdornment position="start">
                                  <KeyIcon />
                                </InputAdornment>
                              }
                              helperText="Name of the output variable"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={5}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Description</InputLabel>
                            <OutlinedInput
                              value={value}
                              onChange={(e) => handleParameterChange(index, 'output_variables', key, e.target.value)}
                              startAdornment={
                                <InputAdornment position="start">
                                  <TextFieldsIcon />
                                </InputAdornment>
                              }
                              helperText="Description of what this output represents"
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            onClick={() => removeParameter(index, 'output_variables', key)}
                            color="error"
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    ))}
                  </AccordionDetails>
                </Accordion>
              </Grid>
            </Grid>
          </Paper>
        ))}
      </Paper>

      <Box display="flex" gap={2}>
        <Button variant="contained" color="primary" type="submit">
          Create Crew
        </Button>
        <Button variant="outlined" onClick={() => navigate('/')}>
          Cancel
        </Button>
      </Box>
    </Box>
  );
}

export default CrewCreate; 