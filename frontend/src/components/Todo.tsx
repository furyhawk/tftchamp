import { useState } from "react";
import * as React from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Container from '@mui/material/Container';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';

import { useStore } from "../store/TodoStore";



function Todo() {
    const [todoText, setTodoText] = useState("");
    const { addTodo, removeTodo, toggleCompletedState, todos } = useStore();

    return (
        <React.Fragment>
            <CssBaseline />
            <Container maxWidth='xs'>
                <Typography variant='h3'>
                    To-Do's
                </Typography>
                <TextField
                    label='Todo Description'
                    required
                    variant='outlined'
                    fullWidth
                    onChange={(e) => setTodoText(e.target.value)}
                    value={todoText}
                />
                <Button
                    fullWidth
                    variant='outlined'
                    color='primary'
                    onClick={() => {
                        if (todoText.length) {
                            addTodo(todoText);
                            setTodoText("");
                        }
                    }}
                >
                    Add Item
                </Button>
                <List>
                    {todos.map((todo) => (
                        <ListItem key={todo.id}>
                            <ListItemIcon>
                                <Checkbox
                                    edge='start'
                                    checked={todo.completed}
                                    onChange={() => toggleCompletedState(todo.id)}
                                />
                            </ListItemIcon>
                            <ListItemText
                                key={todo.id}
                            >
                                {todo.description}
                            </ListItemText>
                            <ListItemSecondaryAction>
                                <Button variant="contained" startIcon={<DeleteIcon />} onClick={() => {
                                    removeTodo(todo.id);
                                }}>Delete</Button>
                            </ListItemSecondaryAction>
                        </ListItem>
                    ))}
                </List>
            </Container>
        </React.Fragment>
    );
}

export default Todo;