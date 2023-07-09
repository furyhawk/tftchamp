import React from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';

import axios from '../services/axios'
import Title from './Title';

import { useMetadataStore } from '../store/MetadataStore';


// interface SelectedDrawerProps {
//     selectedDrawer: string;
// };

// interface ImageType {
//     uri: string;
//     description: string;
// };
// SelectedDrawerProps
// declare const UNDEFINED_VOID_ONLY: unique symbol;
// type Destructor = () => void | { [UNDEFINED_VOID_ONLY]: never };


export default function MediaCard(props) {
    // type image = {
    //     uri: string;
    //     description: string;
    //   };

    const region = useMetadataStore(state => state.region);
    const league = useMetadataStore(state => state.league);
    const latest_version = useMetadataStore(state => state.latest_version);
    const latest_patch = useMetadataStore(state => state.latest_patch);
    const setVersion = useMetadataStore(state => state.setVersion);
    const setPatch = useMetadataStore(state => state.setPatch);

    const [images, setImages] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        let canceled = false;
        setIsLoading(true);

        const metadataBase = `/metadata`;
        const imageBase = `/image/`;
        const imageQuery = `?platform=${region}&league=${league}&version=${latest_version}&patch=${latest_patch}`;
        const uri = `${imageBase}${imageQuery}`;

        async function getImages(uri) {
            if (!canceled) {

                const metadata_response = await axios.get(metadataBase);
                const metadata = metadata_response.data;
                setVersion(metadata.latest_version);
                setPatch(metadata.latest_patch);

                const response = await axios.get(uri);
                const { data } = response;
                setImages(data.results.map(image => ({ ...image, url: `http://${window.location.hostname}:8000` + imageBase + image.uri + imageQuery })));
                setIsLoading(false);
            }
        }

        getImages(uri);
        return () => canceled = true;
    }, [region, league, latest_version, latest_patch, setVersion, setPatch])


    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            {!isLoading ? (
                images.filter((image) => image.uri.toLowerCase().includes(props.selectedDrawer.toLowerCase())).map((image) => (
                    <Card key={image.uri}>
                        <CardContent>
                            <Title>{image.uri}</Title>
                            <Typography variant="body2" color="text.secondary">
                                {image.description}
                            </Typography>
                        </CardContent>
                        <CardMedia
                            component="img"
                            image={image.url}
                            alt={image.uri}
                        />

                        <CardActions>
                            <Button size="small">Share</Button>
                            <Button size="small">Learn More</Button>
                        </CardActions>
                    </Card>
                ))
            ) : (<Skeleton variant="rectangular" width="100%" height={200} />)}
        </Box >
    );
}
