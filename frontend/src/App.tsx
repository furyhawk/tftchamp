import React from 'react';
import { styled, useTheme, Theme, CSSObject } from '@mui/material/styles';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import MuiDrawer from '@mui/material/Drawer';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';

import AlignHorizontalLeftIcon from '@mui/icons-material/AlignHorizontalLeft';
import EngineeringIcon from '@mui/icons-material/Engineering';
import TimelineIcon from '@mui/icons-material/Timeline';
import StackedLineChartIcon from '@mui/icons-material/StackedLineChart';
import TableChartIcon from '@mui/icons-material/TableChart';
import VideogameAssetIcon from '@mui/icons-material/VideogameAsset';
// import Home from '@mui/icons-material/Home';
// import Settings from '@mui/icons-material/Settings';
// import People from '@mui/icons-material/People';
// import PermMedia from '@mui/icons-material/PermMedia';
// import Dns from '@mui/icons-material/Dns';
import InventoryIcon from '@mui/icons-material/Inventory';
// import Public from '@mui/icons-material/Public';
import PsychologyIcon from '@mui/icons-material/Psychology';
// import SortIcon from '@mui/icons-material/Sort';
import TableRowsIcon from '@mui/icons-material/TableRows';
// import { QueryClientProvider, QueryClient } from 'react-query';
// import Dashboard from './components/Dashboard'
// import Person from './components/Person';
// import Todo from './components/Todo'
// import Vote from './components/Vote';
import Match from './components/Match';
import MediaCard from './components/MediaCard';
import Chart from './components/Chart';

import { useMetadataStore } from './store/MetadataStore';

interface MetadataProps {
    sx: any;
    latest_version: string;
    latest_patch: string;
};

function Copyright(props: MetadataProps) {
    return (
        <Typography variant="body2" color="text.secondary" align="center" {...props.sx}>
            {'Copyright © '}
            <Link color="inherit" href="https://github.com/furyhawk/tftchamp/">
                TFTChamp
            </Link>{' '}
            {new Date().getFullYear()}
            {'. '}
            {'Current version: '}{props.latest_version} patched: {props.latest_patch}
        </Typography>
    );
}

const drawerWidth = 240;
// 'Augments', 'Items', 'Composition', 'Feature Importances' 'All matches', 'Recent matches', 'Predict'
const drawerList = [
    { key: 'augment', icon: <AlignHorizontalLeftIcon />, label: 'Augments' },
    { key: 'item', icon: <InventoryIcon />, label: 'Items' },
    { key: 'comp', icon: <TimelineIcon />, label: 'Compositions' },
    { key: 'featureImportance', icon: <StackedLineChartIcon />, label: 'Feature Importances' },
    { key: 'allMatch', icon: <TableChartIcon />, label: 'All matches' },
    { key: 'recentMatch', icon: <TableRowsIcon />, label: 'Recent matches' },
    { key: 'predict', icon: <PsychologyIcon />, label: 'Predict' },
];

const openedMixin = (theme: Theme): CSSObject => ({
    width: drawerWidth,
    transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
    }),
    overflowX: 'hidden',
});

const closedMixin = (theme: Theme): CSSObject => ({
    transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: 'hidden',
    width: `calc(${theme.spacing(7)} + 1px)`,
    [theme.breakpoints.up('sm')]: {
        width: `calc(${theme.spacing(8)} + 1px)`,
    },
});

const DrawerHeader = styled('div')(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
}));

interface AppBarProps extends MuiAppBarProps {
    open?: boolean;
}
const AppBar = styled(MuiAppBar, {
    shouldForwardProp: (prop) => prop !== 'open',
})<AppBarProps>(({ theme, open }) => ({
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(['width', 'margin'], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    ...(open && {
        marginLeft: drawerWidth,
        width: `calc(100% - ${drawerWidth}px)`,
        transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
        }),
    }),
}));

const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
    ({ theme, open }) => ({
        width: drawerWidth,
        flexShrink: 0,
        whiteSpace: 'nowrap',
        boxSizing: 'border-box',
        ...(open && {
            ...openedMixin(theme),
            '& .MuiDrawer-paper': openedMixin(theme),
        }),
        ...(!open && {
            ...closedMixin(theme),
            '& .MuiDrawer-paper': closedMixin(theme),
        }),
    }),
);

function App() {
    // type State = {
    //     region: string;
    //     setRegion: (region: string) => void;
    // };

    const theme = useTheme();
    const [open, setOpen] = React.useState(false);
    const [selectedDrawer, setSelectedDrawer] = React.useState('featureImportance');

    const region = useMetadataStore(state => state.region);
    const setRegion = useMetadataStore(state => state.setRegion);
    const league = useMetadataStore(state => state.league);
    const setLeague = useMetadataStore(state => state.setLeague);
    const latest_version = useMetadataStore(state => state.latest_version);
    const latest_patch = useMetadataStore(state => state.latest_patch);

    const handleListItemClick = (
        event: React.MouseEvent<HTMLDivElement, MouseEvent>,
        index: string,
    ) => {
        setSelectedDrawer(index);
        console.log(index)
    };

    const handleRegionChange = (event: SelectChangeEvent) => {
        setRegion(event.target.value as string);
    };

    const handleLeagueChange = (event: SelectChangeEvent) => {
        setLeague(event.target.value as string);
    };

    const handleDrawerOpen = () => {
        setOpen(true);
    };

    const handleDrawerClose = () => {
        setOpen(false);
    };

    return (

        <Box sx={{ display: 'flex', width: '100%' }}>
            <CssBaseline />
            <AppBar position="fixed" open={open}>
                <Toolbar variant="dense">
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        onClick={handleDrawerOpen}
                        edge="start"
                        sx={{
                            marginRight: 5,
                            ...(open && { display: 'none' }),
                        }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <VideogameAssetIcon sx={{ mr: 2 }} />
                    <Typography variant="h5" color="inherit" component="div">
                        TFTChamp
                    </Typography>
                    <Box sx={{ flexGrow: 1 }} />
                    <FormControl variant="standard" sx={{ m: 1, minWidth: 140 }}>
                        <InputLabel id="region-simple-select-label">Region</InputLabel>
                        <Select
                            labelId="region-simple-select-label"
                            id="region-simple-select"
                            value={region}
                            label="Region"
                            onChange={handleRegionChange}
                        >
                            <MenuItem value='na1'>NA1</MenuItem>
                            <MenuItem value='kr'>KR</MenuItem>
                            <MenuItem value='euw1'>EUW1</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl variant="standard" sx={{ m: 1, minWidth: 140 }}>
                        <InputLabel id="league-simple-select-label">Region</InputLabel>
                        <Select
                            labelId="league-simple-select-label"
                            id="league-simple-select"
                            value={league}
                            label="League"
                            onChange={handleLeagueChange}
                        >
                            <MenuItem value='challengers'>Challengers</MenuItem>
                            <MenuItem value='grandmasters'>Grandmasters</MenuItem>
                            <MenuItem value='masters'>Masters</MenuItem>
                        </Select>
                    </FormControl>
                </Toolbar>
            </AppBar>
            <Drawer variant="permanent" open={open}>
                <DrawerHeader>
                    <IconButton onClick={handleDrawerClose}>
                        {theme.direction === 'rtl' ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                    </IconButton>
                </DrawerHeader>
                <Divider />
                <List>
                    {drawerList.map((drawer, index) => (
                        <ListItem key={drawer.key} disablePadding sx={{ display: 'block' }}>
                            <Tooltip title={drawer.label} placement="right" arrow>
                                <ListItemButton
                                    sx={{
                                        minHeight: 48,
                                        justifyContent: open ? 'initial' : 'center',
                                        px: 2.5,
                                    }}
                                    onClick={(event) => handleListItemClick(event, drawer.key)}
                                    selected={selectedDrawer === drawer.key}
                                >
                                    <ListItemIcon
                                        sx={{
                                            minWidth: 0,
                                            mr: open ? 3 : 'auto',
                                            justifyContent: 'center',
                                        }}
                                    >
                                        {drawerList[index].icon}
                                    </ListItemIcon>
                                    <ListItemText primary={drawer.label} sx={{ opacity: open ? 1 : 0 }} />
                                </ListItemButton>
                            </Tooltip>
                        </ListItem>
                    ))}
                </List>
                <Divider />
            </Drawer>

            <Container sx={{ width: '100%', mt: 4, mb: 4 }}>
                <DrawerHeader />
                <Grid container spacing={3} sx={{ width: '100%' }}>
                    {/* Chart */}
                    {selectedDrawer === 'featureImportance' ? (
                        <Grid item xs={12} sx={{ width: '100%' }}>
                            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                                <Chart />
                            </Paper>
                        </Grid>
                    ) : null}
                    {/* Top5 Tables */}
                    {(selectedDrawer === 'augment' || selectedDrawer === 'item' || selectedDrawer === 'comp') ? (
                        <Grid item xs={12} sx={{ width: '100%' }}>
                            <MediaCard selectedDrawer={selectedDrawer} />
                        </Grid>
                    ) : null}
                    {/* Recent Matches */}
                    {(selectedDrawer === 'allMatch' || selectedDrawer === 'recentMatch') ? (
                        <Grid item xs={12} sx={{ width: '100%' }}>
                            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                                <Match />
                            </Paper>
                        </Grid>
                    ) : null}
                    {(selectedDrawer === 'predict') ? (
                        <Grid item xs={12} sx={{ width: '100%' }}>
                            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                                WIP <EngineeringIcon /> {latest_version}
                            </Paper>
                        </Grid>
                    ) : null}
                </Grid>
                <Copyright sx={{ pt: 4 }} latest_version={latest_version} latest_patch={latest_patch} />
            </Container>
        </Box >

    );
}


export default App;