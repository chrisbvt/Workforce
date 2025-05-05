import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function CrewExecutions() {
  const { crewId } = useParams();
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

  useEffect(() => {
    fetchExecutions();
  }, [crewId]);

  const fetchExecutions = async () => {
    try {
      const response = await axios.get(`${API_URL}/crews/${crewId}/executions`);
      setExecutions(response.data.executions);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch executions');
      setLoading(false);
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
      <Typography variant="h4" gutterBottom>
        Crew Executions
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created At</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {executions.map((execution) => (
              <TableRow key={execution.id}>
                <TableCell>{execution.id}</TableCell>
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

      {/* Execution Details Dialog */}
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
              <Typography variant="subtitle1" gutterBottom>
                Status: {selectedExecution.status}
              </Typography>
              
              {selectedExecution.error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {selectedExecution.error}
                </Alert>
              )}

              {selectedExecution.input_variables && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Input Variables
                  </Typography>
                  <Paper sx={{ p: 2 }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(selectedExecution.input_variables, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}

              {selectedExecution.task_params && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Task Parameters
                  </Typography>
                  <Paper sx={{ p: 2 }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(selectedExecution.task_params, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}

              {selectedExecution.result && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Result
                  </Typography>
                  <Paper sx={{ p: 2 }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(selectedExecution.result, null, 2)}
                    </pre>
                  </Paper>
                </Box>
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

export default CrewExecutions; 