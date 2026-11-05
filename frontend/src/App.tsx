import { Header } from '@/components/Header';
import { DraftSavedPage, NotFoundPage, ProductListPage, ProductPage } from '@/pages';
import { Route, Switch } from 'wouter';

function App() {
  return (
    <div className="h-screen flex flex-col">
      <Header />

      <Switch>
        <Route path="/">
          <ProductListPage />
        </Route>
        <Route path="/product/new/saved">
          <DraftSavedPage />
        </Route>
        <Route path="/product/new" nest>
          <ProductPage mode="create" />
        </Route>
        <Route path="/product/:id/saved">
          <DraftSavedPage />
        </Route>
        <Route path="/product/:id" nest>
          <ProductPage mode="edit" />
        </Route>

        <Route>
          <NotFoundPage />
        </Route>
      </Switch>
    </div>
  );
}

export default App;
